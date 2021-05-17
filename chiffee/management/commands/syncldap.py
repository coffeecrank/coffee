import logging

import ldap
from django.conf import settings
from django.core.management.base import BaseCommand
from django_auth_ldap.backend import LDAPBackend

from chiffee.models import User

logger = logging.getLogger('syncldap')


class Command(BaseCommand):
    help = 'Sync local users with the LDAP server'

    def handle(self, *args, **options):
        self.__class__._sync_users()
        self.__class__._find_inactive_users()

    @staticmethod
    def _sync_users():
        connection = ldap.initialize(settings.AUTH_LDAP_SERVER_URI)
        connection.simple_bind_s(settings.AUTH_LDAP_BIND_DN,
                                 settings.AUTH_LDAP_BIND_PASSWORD)
        ldap_users = connection.search_s(settings.BASE_DN,
                                         ldap.SCOPE_SUBTREE,
                                         '(objectClass=posixAccount)')
        connection.unbind()

        for ldap_user in ldap_users:
            user_id = ldap_user[1]['uid'][0].decode('UTF-8')

            if not User.objects.filter(username=user_id).exists():
                logger.info(f'Adding new user {user_id}...')

            user = LDAPBackend().populate_user(user_id)
            user.is_active = True

            if len(user.groups.all()) == 0:
                logger.info(f'No groups were found for {user_id}.')

            user.save()

    @staticmethod
    def _find_inactive_users():
        for user in User.objects.filter(is_active=True):
            ldap_user = LDAPBackend().populate_user(user.username)

            if ldap_user is None:
               user.is_active = False
               user.save()
               logger.info(f'User {user.username} was set to inactive.')
