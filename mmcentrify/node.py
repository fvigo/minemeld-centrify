import logging
import json
import yaml
import os
import datetime
from mmcentrify import centrify as centrify

from minemeld.ft.actorbase import ActorBaseFT
import minemeld.ft.base as base

LOG = logging.getLogger(__name__)

# Centrify Output Node for MineMeld
class CentrifyOutput(ActorBaseFT):
    def configure(self):
        super(CentrifyOutput, self).configure()
    
        self.centrifytarget = {
            'tenant' : None,
            'token' : None
        }

        self.auth_cookie_timestamp = None
    
        # Load Side Config
        self.side_config_path = self.config.get('side_config', None)
        if self.side_config_path is None:
            self.side_config_path = os.path.join(
                os.environ['MM_CONFIG_DIR'],
                '%s_side_config.yml' % self.name
            )

        self._load_side_config()

        # Load Auth Cookie
        self.auth_cookie_file_path = self.config.get('auth_cookie_file', None)
        if self.auth_cookie_file_path is None:
            self.auth_cookie_file_path = os.path.join(
                os.environ['MM_CONFIG_DIR'],
                '%s_auth_cookie.yml' % self.name
                )

        self._load_auth_cookie()

    def _load_side_config(self):
        try:
            with open(self.side_config_path, 'r') as f:
                sconfig = yaml.safe_load(f)

        except Exception as e:
            LOG.error('{} - Error loading side config: {}'.format(self.name, str(e)))
            return

        # Centrify Endpoint Configuration
        self.centrifytarget = {
            'tenant' : sconfig.get('centrify_tenant', None),
            'token' : None
        }

        # Centrify API user and password
        self.centrify_user = sconfig.get('centrify_user', None)
        self.centrify_password = sconfig.get('centrify_password', None)

        # Centrify role name (not ID) to assign users to
        self.quarantine_role = sconfig.get('quarantine_role', None)

        # Default domain if username indicator does not contain it
        self.default_domain = sconfig.get('default_domain', None)

        # Authentication Cookie Timeout (in hours, default 12)
        self.auth_timeout = sconfig.get('auth_timeout', 12)

    def _load_auth_cookie(self):
        try:
            with open(self.auth_cookie_file_path, 'r') as f:
                cookiefile = yaml.safe_load(f)

        except Exception as e:
            LOG.error('{} - Error loading auth cookie: {}'.format(self.name, str(e)))
            return

        # Centrify Cookie and Last Auth Timestamp
        self.centrifytarget['token'] = cookiefile.get('auth_cookie', None)
        self.auth_cookie_timestamp = cookiefile.get('auth_cookie_timestamp', None)

    # Determine if authentication is needed
    def _is_auth_needed(self):
        now = datetime.datetime.now()
        auth_needed = True

        if self.centrifytarget['token'] is None:
            return auth_needed

        if self.auth_cookie_timestamp is None:
            return auth_needed

        delta = now - self.auth_cookie_timestamp
        if delta < datetime.timedelta(hours=self.auth_timeout):
            auth_needed = False

        return auth_needed

    def _save_auth_cookie(self):
        cookie = {
            'auth_cookie': self.centrifytarget['token'],
            'auth_cookie_timestamp': self.auth_cookie_timestamp
        }

        try:
            with open(self.auth_cookie_file_path, 'w') as f:
                yaml.dump(cookie, f, default_flow_style=False)

        except Exception as e:
            LOG.error('{} - Error writing on auth cookie file: {}'.format(self.name, str(e)))
            return


    def hup(self, source=None):
        LOG.info('{} - hup received, reload side config'.format(self.name))
        self._load_side_config()
        super(CentrifyOutput, self).hup(source)

    @base._counting('update.processed')
    def filtered_update(self, source=None, indicator=None, value=None):
        if self.centrify_user is None:
            raise RuntimeError('{} - Centrify API Username not set'.format(self.name))

        if self.centrify_password is None:
            raise RuntimeError('{} - Centrify API Password not set'.format(self.name))

        if self.centrifytarget['tenant'] is None:
            raise RuntimeError('{} - Centrify Tenant not set'.format(self.name))

        # Work exclusively with user-id indicators
        if(value['type'] != 'user-id'):
            LOG.debug('{} - Received Indicator of type {}, expecting user-id, skipping'.format(self.name, value['type']))
            return

        # Authenticate if required
        if self._is_auth_needed():
            now = datetime.datetime.now()
            # Function will return only if authentication is successful, otherwise will throw an exception
            cookie = centrify.authenticate(self.centrifytarget, self.centrify_user, self.centrify_password)
            self.centrifytarget['token'] = cookie
            self.auth_cookie_timestamp = now
            self._save_auth_cookie()

        # Add user to Quarantine Role
        if self.quarantine_role is not None:
            centrify.lookup_and_add(self.centrifytarget, centrify.domain_normalize(indicator, None, self.default_domain), self.quarantine_role)
    

    @base._counting('withdraw.processed')
    def filtered_withdraw(self, source=None, indicator=None, value=None):
        if self.centrify_user is None:
            raise RuntimeError('{} - Centrify API Username not set'.format(self.name))

        if self.centrify_password is None:
            raise RuntimeError('{} - Centrify API Password not set'.format(self.name))

        if self.centrifytarget['tenant'] is None:
            raise RuntimeError('{} - Centrify Tenant not set'.format(self.name))

        # Work exclusively with user-id indicators
        if(value['type'] != 'user-id'):
            LOG.debug('{} - Received Indicator of type {}, expecting user-id, skipping'.format(self.name, value['type']))
            return

        # Authenticate if required
        if self._is_auth_needed():
            now = datetime.datetime.now()
            # Function will return only if authentication is successful, otherwise will throw an exception
            cookie = centrify.authenticate(self.centrifytarget, self.centrify_user, self.centrify_password)
            self.centrifytarget['token'] = cookie
            self.auth_cookie_timestamp = now
            self._save_auth_cookie()

        # Remove user to Quarantine Role
        if self.quarantine_role is not None:
            centrify.lookup_and_remove(self.centrifytarget, centrify.domain_normalize(indicator, None, self.default_domain), self.quarantine_role)
