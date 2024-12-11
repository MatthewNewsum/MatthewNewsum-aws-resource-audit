from typing import Dict, List, Any
from .base import AWSService

class IAMService(AWSService):
    @property
    def service_name(self) -> str:
        return 'iam'

    def audit(self) -> Dict[str, List[Dict[str, Any]]]:
        return {
            'users': self._audit_users(),
            'roles': self._audit_roles(),
            'groups': self._audit_groups()
        }

    def _audit_users(self) -> List[Dict[str, Any]]:
        users = []
        paginator = self.client.get_paginator('list_users')
        
        for page in paginator.paginate():
            for user in page['Users']:
                access_keys = self.client.list_access_keys(UserName=user['UserName'])['AccessKeyMetadata']
                mfa_devices = self.client.list_mfa_devices(UserName=user['UserName'])['MFADevices']
                groups = self.client.list_groups_for_user(UserName=user['UserName'])['Groups']
                
                active_key_last_used = self._get_key_last_used(access_keys)
                
                users.append({
                    'UserName': user['UserName'],
                    'UserId': user['UserId'],
                    'ARN': user['Arn'],
                    'Created': str(user['CreateDate']),
                    'PasswordLastUsed': str(user.get('PasswordLastUsed', 'Never')),
                    'AccessKeysActive': len([k for k in access_keys if k['Status'] == 'Active']),
                    'AccessKeysLastUsed': ', '.join(active_key_last_used) if active_key_last_used else 'N/A',
                    'MFAEnabled': len(mfa_devices) > 0,
                    'GroupMemberships': ', '.join([g['GroupName'] for g in groups])
                })
                
        return users

    def _get_key_last_used(self, access_keys: List[Dict[str, Any]]) -> List[str]:
        last_used = []
        for key in access_keys:
            if key['Status'] == 'Active':
                try:
                    key_info = self.client.get_access_key_last_used(AccessKeyId=key['AccessKeyId'])
                    last_used_date = key_info.get('AccessKeyLastUsed', {}).get('LastUsedDate', 'Never')
                    last_used.append(str(last_used_date))
                except Exception:
                    last_used.append('Error getting last used date')
        return last_used

    def _audit_roles(self) -> List[Dict[str, Any]]:
        roles = []
        paginator = self.client.get_paginator('list_roles')
        
        for page in paginator.paginate():
            for role in page['Roles']:
                roles.append({
                    'RoleName': role['RoleName'],
                    'RoleId': role['RoleId'],
                    'ARN': role['Arn'],
                    'Created': str(role['CreateDate']),
                    'Description': role.get('Description', 'N/A'),
                    'MaxSessionDuration': role.get('MaxSessionDuration', 3600),
                    'Path': role.get('Path', '/'),
                    'ServiceLinked': role.get('Path', '/').startswith('/aws-service-role/')
                })
                
        return roles

    def _audit_groups(self) -> List[Dict[str, Any]]:
        groups = []
        paginator = self.client.get_paginator('list_groups')
        
        for page in paginator.paginate():
            for group in page['Groups']:
                members = self.client.get_group(GroupName=group['GroupName'])['Users']
                
                groups.append({
                    'GroupName': group['GroupName'],
                    'GroupId': group['GroupId'],
                    'ARN': group['Arn'],
                    'Created': str(group['CreateDate']),
                    'MemberCount': len(members),
                    'Members': ', '.join([u['UserName'] for u in members]),
                    'Path': group.get('Path', '/')
                })
                
        return groups