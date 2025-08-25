import requests
import json
from datetime import datetime, timedelta
from msal import PublicClientApplication
import threading

application_id = "" # REQUIRED : The ID of the application registration listed in Azure.
base_url = 'https://graph.microsoft.com/v1.0/'
beta_url = 'https://graph.microsoft.com/beta/'
authority_url = 'https://login.microsoftonline.com/0000-0000' # Makes auth easier just linking the tenant ID in the authority URL. You can use the common one but update this and compile.
# authority_url = 'https://login.microsoftonline.com/common'
scope = ['User.Read', 'RoleManagement.ReadWrite.Directory','PrivilegedEligibilitySchedule.ReadWrite.AzureADGroup'] # REQUIRED : The permissions you'll need to give to your app registration in Azure.

class graph_initialize():
    headers: str = ""
    refresh_token: str = ""
    user_id: str = ""
    mutex = threading.Lock()
    last_auth_time = ""
    
    def __init__(self):
        return
    
    def __del__(self):
        print("...Disconnect...")

    # New method to auth.
    def get_auth(self) -> dict:
        result = None
        self.app =  PublicClientApplication(
            application_id,
            authority=authority_url
        )
        claims = {
            "access_token": {
                "acrs": {
                    "essential": True,
                    "value": "c1"
                    }
            }
        }
        claims = json.dumps(claims)
        try:
            result = self.app.acquire_token_interactive(scopes=scope, claims_challenge=claims)
            # result = result.json()
            access_token_id = result['access_token']
            self.headers = {'Authorization': 'Bearer ' + access_token_id}
            print(result)
            b = {"Status": "Checkout success", "Error": ""}
            b['Error'] = "Token aquired without issue"
            return(b)
        except Exception as e:
            a = {"Status": "Token failed", "Error": ""}
            a['Error'] = e
            return(a)
     
    # A secondary auth methoded used if POST requests return a certain error. This forces login re-entry ignoring browser sessions. Therefore reauth on the account allowing some roles/groups/resoruces that have the "Force Reauthentication" checkmark enabled.
    def get_auth_force_prompt(self):
        with self.mutex:
            if self.last_auth_time == "" or self.last_auth_time < (datetime.now() - timedelta(minutes=10)):
                result = None
                self.app =  PublicClientApplication(
                    application_id,
                    authority=authority_url
                )
                claims = {
                    "access_token": {
                        "acrs": {
                            "essential": True,
                            "value": "c1"
                            }
                    }
                }
                claims = json.dumps(claims)
                try:
                    result = self.app.acquire_token_interactive(scopes=scope, claims_challenge=claims, prompt='login')
                    self.last_auth_time = datetime.now() # sets last_auth_time to now so if this function was ran in the last XX minutes it won't run again.
                    access_token_id = result['access_token']
                    self.headers = {'Authorization': 'Bearer ' + access_token_id}
                    print(result)
                    b = {"Status": "Checkout success", "Error": ""}
                    b['Error'] = "Token aquired without issue"
                    return(b)
                except Exception as e:
                    a = {"Status": "Token failed", "Error": ""}
                    a['Error'] = e
                    return(a)
            else:
                print("Failed if during forced reauth.")
        
    def get_personaldata(self) -> str:
        if self.user_id != "":
            return self.user_id
        endpoint = base_url + 'me'
        response = requests.get(endpoint, headers=self.headers)
        self.user_id = response.json()
        # print(self.user_id)
        return(self.user_id)
    
    def get_roles(self):
        if self.headers:
            d = self.get_personaldata()
            endpoint = base_url + f"roleManagement/directory/roleEligibilitySchedules?$filter=principalId eq '{d['id']}'&$expand=roleDefinition"
            response = requests.get(endpoint, headers=self.headers)
            self.allroles = response
            return(response.json())
    
    def get_active_roles(self):
        if self.headers:
            d = self.get_personaldata()
            endpoint = base_url + f"roleManagement/directory/roleAssignmentSchedules?$filter=principalId+eq+'{d['id']}'&$expand=roleDefinition "
            response = requests.get(endpoint, headers=self.headers)
            # self.allroles = response
            return(response.json())
    
    # This specific command uses the beta branch. Hopefully this doesnt just stop working one day.... it will knowing Microsoft. 
    def get_groups(self):
        if self.headers:
            d = self.get_personaldata()
            endpoint = f"https://graph.microsoft.com/beta/identityGovernance/privilegedAccess/group/eligibilitySchedules?filter=principalId eq '{d['id']}'&$expand=group"
            response = requests.get(endpoint, headers=self.headers)
            self.allroles = response
            print(response)
            return(response.json())
        
    def get_active_groups(self):
        if self.headers:
            d = self.get_personaldata()
            endpoint = f"https://graph.microsoft.com/v1.0/identityGovernance/privilegedAccess/group/assignmentScheduleInstances?$filter=principalId eq '{d['id']}'&$expand=group"
            response = requests.get(endpoint, headers=self.headers)
            # self.allroles = response
            print(response)
            return(response.json())
        
    def get_resources(self):
        if self.headers:
            d = self.get_personaldata()
            endpoint = beta_url + f"privilegedAccess/azureResources/roleAssignments?$filter=subjectId+eq+'{d['id']}'&$expand=resource,roleDefinition"
            response = requests.get(endpoint, headers=self.headers)
            self.allresources = response
            print(response)
            return(response.json())
        
    def get_active_resources(self):
        if self.headers:
            endpoint = beta_url + "privilegedAccess/azureResources/resources?$filter=(type+eq+'resourcegroup' or type+eq+'subscription')"
            response = requests.get(endpoint, headers=self.headers)
            # self.allroles = response
            print(response)
            return(response.json())    
        
    def checkout_roles(self, role: str) -> dict:
        d = self.get_personaldata()
        role_list = self.allroles.json()
        for i in role_list['value']:
            if i['roleDefinition']['displayName'] == role:
                print(f"Match: {i['roleDefinition']['displayName']} and {role}")
                print(i['roleDefinitionId'])
                c = i
                
        body = {
            "action": "selfActivate",
            "PrincipalId": "",
            "Justification": "Needed for work.",
            "RoleDefinitionId": "",
            "DirectoryScopeId": "",
            "scheduleInfo": {
                "StartDateTime": "2025-06-25T14:30:00Z",
                "Expiration": {
                    "Type": "AfterDuration",
                    "Duration": ""
                }
            }
        }
        body['PrincipalId'] = d['id']
        body['RoleDefinitionId'] = c['roleDefinitionId']
        body['DirectoryScopeId'] = c['directoryScopeId']
        body['scheduleInfo']['Expiration']['Duration'] = "PT8H"
        
        try:
            endpoint = base_url + f"roleManagement/directory/roleAssignmentScheduleRequests"
            response = requests.post(endpoint, headers=self.headers, json=body)
            print(f"Role Checkout: {response}")
            t = response.json()
            # This if statement catches if the failure is due to requesting too much duration. Some roles have a maximum checkout time and if you ask for more the request will fail. This readjusts it to 4 hours and tries again.
            if t['error']['message'] == "The following policy rules failed: [\"ExpirationRule\"]":
                print("Trying 4 hours.")
                body['scheduleInfo']['Expiration']['Duration'] = "PT4H"

                endpoint = base_url + f"roleManagement/directory/roleAssignmentScheduleRequests"
                response = requests.post(endpoint, headers=self.headers, json=body)
                print(f"Role Checkout 4H: {response}")
                t = response.json()
                a = {"Status": "Checkout Succeeded", "Error": ""}
                a['Error'] = "Checkout succeeded without issue"
                return(a)
            
            # This if is a catch all for any bad requests. This shouldnt happen as all other stements should be accounted for but if it happens it's usually due to a bad token.
            elif t['error']['code'] == "BadRequest":
                a = {"Status": "Checkout Failed", "Error": ""}
                a['Error'] = "Checkout Failed due to BadRequest. Try acquiring a new token"
                return(a)
            
            # This if is to check for reauth requirements when checking out a role. If a role has "Require reauth" enabled it'll spit out this response after the initial account sigin with MFA, usually 15 minutes.
            elif t['error']['code'] == "RoleAssignmentRequestAcrsValidationFailed":
                # print(self.headers)
                reauthsponse = self.get_auth_force_prompt()
                print(reauthsponse)
                # print(self.headers)
                if reauthsponse['Status'] == "Token failed":
                    a = {"Status": "Checkout Failed", "Error": ""}
                    a['Error'] = "Checkout Failed due to expired MFA ARCS token. Sign out of the browser and sign in again, then retrieve a new token in app. This is due to certain roles requiring reauth and MFA expires after 15 minutes of initial sign in."
                    return(a)
                elif reauthsponse['Status'] == "Checkout success":
                    body['scheduleInfo']['Expiration']['Duration'] = "PT4H"
                    endpoint = base_url + f"roleManagement/directory/roleAssignmentScheduleRequests"
                    response = requests.post(endpoint, headers=self.headers, json=body)
                    print(f"Role Checkout 4H and reauth: {response}")
                    t = response.json()
                    print(t)
                    a = {"Status": "Checkout Succeeded", "Error": ""}
                    a['Error'] = "Checkout succeeded without issue"
                    return(a)
                
            # This final else in the initial if just catches the request if it does not meet any of the failures listed above. This would happen if the sucess was good.  
            else:
                print(t)
                a = {"Status": "Checkout Succeeded", "Error": ""}
                a['Error'] = "Checkout succeeded without issue"
                return(a)
        except Exception as e:
            a = {"Status": "Checkout Succeeded", "Error": ""}
            a['Error'] = "Chekcout succeeded without issue"
            return(a)

    def checkout_resources(self, role: str) -> dict:
        d = self.get_personaldata()
        resource_list = self.allresources.json()
        for i in resource_list['value']:
            if i['resource']['displayName'] == role:
                print(f"Match: {i['roleDefinition']['displayName']} and {role}")
                print(i['roleDefinitionId'])
                c = i
            else:
                print(f"Failed to set C for I... {i}")
                
        body = {
            "roleDefinitionId": "",
            "resourceId": "",
            "subjectId": "",
            "assignmentState": "Active",
            "type": "UserAdd",
            "reason": "PIM Activation Toolkit",
            "schedule": {
                "Duration": "",
                "type": "Once"
            }
        }
        print(c)
        body['roleDefinitionId'] = c['roleDefinitionId']
        body['resourceId'] = c['resourceId']
        body['subjectId'] = d['id']
        body['schedule']['Duration'] = "PT8H"
        
        try:
            endpoint = beta_url + f"privilegedAccess/azureResources/roleAssignmentRequests"
            response = requests.post(endpoint, headers=self.headers, json=body)
            print(f"Resource Checkout: {response}")
            t = response.json()
            if t['error']['message'] == "The following policy rules failed: [\"ExpirationRule\"]":
                print("Trying 4 hours.")
                body['schedule']['Duration'] = "PT4H"

                endpoint = beta_url + f"privilegedAccess/azureResources/roleAssignmentRequests"
                response = requests.post(endpoint, headers=self.headers, json=body)
                print(f"Resource Checkout 4H: {response}")
                t = response.json()
                a = {"Status": "Checkout Succeeded", "Error": ""}
                a['Error'] = "Checkout succeeded without issue"
                return(a)
            elif t['error']['code'] == "BadRequest":
                a = {"Status": "Checkout Failed", "Error": ""}
                a['Error'] = "Checkout Failed due to BadRequest. Try acquiring a new token"
                return(a)
            else:
                # print(t)
                a = {"Status": "Checkout Succeeded", "Error": ""}
                a['Error'] = "Checkout succeeded without issue"
                return(a)
        except Exception as e:
            a = {"Status": "Checkout Succeeded", "Error": ""}
            a['Error'] = "Chekcout succeeded without issue"
            return(a)