import graphene
from userManage.schema import UserManageQuery, UserManageMutation
# from internshipManage.schema import InternshipQuery, InternshipMutation

class Query(UserManageQuery, graphene.ObjectType):
    pass
class Mutation(UserManageMutation, graphene.ObjectType):
    pass

schema = graphene.Schema(query=Query, mutation=Mutation)