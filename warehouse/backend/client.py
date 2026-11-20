import requests
URL = "http://127.0.0.1:8000"
user_credentials = {"username": "milky", "password": "2357", "user_type": "manager"}
response = requests.post(url=URL+"/register", json=user_credentials)
print(response.status_code)
print(response.json())

response = requests.post(url=URL+"/login", json=user_credentials)
response_json = response.json()
access_token = response_json["access_token"]
refresh_token = response_json["refresh_token"]

header = {"token": access_token}
response = requests.get(url=URL+"/packages", headers=header)
print(response.status_code)
print(response.json())

parameters = {"package_name": "new_package", "destination": "new_destination", "weight": 10, "arrival_date": "2024-06-01"}
response = requests.post(url=URL+"/packages", headers=header, json=parameters)
print(response.status_code)
print(response.json())

package_id = int(input())    
response = requests.get(url=URL+"/packages/{package_id}", headers=header)
print(response.status_code)
print(response.json())

# parameters = {"package_name": "new_package", "destination": "new_destination", "weight": 10, "arrival_date": "2024-06-01"}
# response = requests.patch(url=URL+"/packages/{package_id}", headers=header, json=parameters)
# print(response.status_code)
# print(response.json())

# response = requests.delete(url=URL+"/packages/{package_id}", headers=header)
# print(response.status_code)
# print(response.json())

# response = requests.get(url=URL+"/dispatch-batches", headers=header)
# print(response.status_code)
# print(response.json())

# status = input("Enter status: ")
# response = requests.post(url=URL+"/dispatch-batches", headers=header, json=status)
# print(response.status_code)
# print(response.json())

# response = requests.get(url=URL+"/warehouses/statistics", headers=header)
# print(response.status_code)
# print(response.json())

# response = requests.patch(url=URL+"/dispatch-batches/{batch_id}", headers=header, json=status)
# print(response.status_code)
# print(response.json())

