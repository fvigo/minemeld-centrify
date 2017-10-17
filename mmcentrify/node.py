import logging
import json
import yaml
import os
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
            'user' : None,
            'password' : None
        }
    
        # Load Side Config
        self.side_config_path = self.config.get('side_config', None)
        if self.side_config_path is None:
            self.side_config_path = os.path.join(
                os.environ['MM_CONFIG_DIR'],
                '%s_side_config.yml' % self.name
            )

        self._load_side_config()

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
            'user' : sconfig.get('centrify_user', None),
            'password' : sconfig.get('centrify_password', None),
        }

        # Centrify role name (not ID) to assign users to
        self.quarantine_role = sconfig.get('quarantine_role', None)

    def hup(self, source=None):
        LOG.info('{} - hup received, reload side config'.format(self.name))
        self._load_side_config()
        super(CentrifyOutput, self).hup(source)

    @base._counting('update.processed')
    def filtered_update(self, source=None, indicator=None, value=None):
        if self.centrifytarget['user'] is None:
            raise RuntimeError('{} - Centrify Username not set'.format(self.name))

       if self.centrifytarget['password'] is None:
            raise RuntimeError('{} - Centrify Password not set'.format(self.name))

       if self.centrifytarget['tenant'] is None:
            raise RuntimeError('{} - Centrify Tenant not set'.format(self.name))

        # Work exclusively with user-id indicators
        if(value['type'] != 'user-id'):
            LOG.debug('{} - Received Indicator of type {}, expecting user-id, skipping'.format(self.name, value['type']))
            return

        # Lookup user
        user = centrify.lookup_user(self.centrifytarget, indicator)

        # Add user to Group
        if self.quarantine_role is not None:
            roleid = centrify.lookup_role(self.centrifytarget, self.quarantine_role)
            centrify.add_user_to_role(self.centrifytarget, user, roleid)

    @base._counting('withdraw.processed')
    def filtered_withdraw(self, source=None, indicator=None, value=None):
        if self.centrifytarget['user'] is None:
            raise RuntimeError('{} - Centrify Username not set'.format(self.name))

        if self.centrifytarget['password'] is None:
            raise RuntimeError('{} - Centrify Password not set'.format(self.name))

       if self.centrifytarget['tenant'] is None:
            raise RuntimeError('{} - Centrify Tenant not set'.format(self.name))

        # Work exclusively with user-id indicators
        if(value['type'] != 'user-id'):
            LOG.debug('{} - Received Indicator of type {}, expecting user-id, skipping'.format(self.name, value['type']))
            return

        # Lookup user
        user = centrify.lookup_user(self.centrifytarget, indicator)

        # Remove user from  Group
        if self.quarantine_role is not None:
            roleid = centrify.lookup_role(self.centrifytarget, self.quarantine_role)
            centrify.remove_user_from_role(self.centrifytarget, user, roleid)

