# -*- encoding: utf-8 -*-
#
#    Module Writen to OpenERP, Open Source Management Solution
#
#    Copyright (c) 2014 Vauxoo - http://www.vauxoo.com/
#    All Rights Reserved.
#    info Vauxoo (info@vauxoo.com)
#
#    Coded by: Luis Torres (luis_t@vauxoo.com)
#
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''
    This file is used to add the field lang in runbot.build and the function
    that install and assign the language to the users in the instance generated.
'''
from openerp.osv import fields, osv
import oerplib
from openerp import tools
import logging

class runbot_repo(osv.osv):
    '''
    Inherit class runbot_repo to add field to select the language that must be assigned to builds 
    that genere the repo.
    '''
    _inherit = "runbot.repo"

    _columns = {
        'lang': fields.selection(tools.scan_languages(), 'Language', help='Language to change '
                                 'instance after of run test.', copy=True),
    }

class runbot_build(osv.osv):
    '''
    Inherit class runbot_build to add field to select the language & the function with a job
    to install and assign the language to users if this is captured too is added with an super the 
    function create to assign the language from repo in the builds.
    '''
    _inherit = "runbot.build"

    _columns = {
        'lang': fields.selection(tools.scan_languages(), 'Language', help='Language to change '
                                 'instance after of run test.', copy=True),
    }
    
    def create(self, cr, uid, values, context=None):
        """
        This method set language from repo in the build.
        """
        new_id = super(runbot_build, self).create(cr, uid, values, context=context)
        lang = self.read(cr, uid, [new_id], ['lang'], context=context)[0]['lang']
        if values.get('branch_id', False) and not lang:
            branch_id = self.pool.get('runbot.branch').browse(cr, uid,
                                                              values['branch_id'])
            build_id = self.search(cr, uid, [('branch_id', '=', values['branch_id'])])
            self.write(cr, uid, build_id, {'lang': branch_id.repo_id and \
                 branch_id.repo_id.lang or False}, context=context)
        return new_id

    def job_50_load_lang(self, cr, uid, build, lock_path, log_path):
        """
        This method is used to install a lang if this not is installed and assign this to the users
        in the instances that generated runbot.

        :param build: object build of runbot.
        :param lock_path: path of lock file, this parameter is string.
        :param log_path: path of log file, this parameter is string, where are
                            has saved the log of test.
        """
        _logger = logging.getLogger("runbot-job")
        _logger.info(
            "start with the process that load and assign translation...")
        db_name = build.dest + '-all'
        port = build.port
        user = 'admin'
        passwd = 'admin'
        server = 'localhost'
        code_lang = build.lang
        connect = oerplib.OERP(
            server=server,
            database=db_name,
            port=port,
            timeout=10,
        )

        connect.login(user, passwd)
        connect.config['timeout'] = 300
        if code_lang:
            lang_id = connect.search('res.lang', [('code', '=', code_lang)])
            if not lang_id:
                base_lang_obj = connect.get('base.language.install')
                try:
                    _logger.info('install the language %s...' % (code_lang,))
                    lang_create_id = connect.create(
                        'base.language.install', {'lang': code_lang, })
                    base_lang_obj.lang_install([lang_create_id])
                except Exception as exception:
                    _logger.error(exception.oerp_traceback)
                lang_id = connect.search('res.lang', [
                    ('code', '=', code_lang)])
            if lang_id:
                _logger.info('assign the language to users in the instance...')
                connect.write('res.users', connect.search(
                    'res.users', []), {'lang': code_lang})