from graphql_jwt.utils import jwt_payload

def custom_jwt_payload(user, context=None):
    payload = jwt_payload(user) 
    payload['user_id'] = user.id
    payload['username'] = user.username
    payload['email'] = user.email
    payload['role'] = user.role
    return payload