import graphene
from userManage.schema import UserManageQuery, UserManageMutation
from internshipManage.schema import InternshipQuery, InternshipMutation

class Query(UserManageQuery, InternshipQuery, graphene.ObjectType):
    pass
class Mutation(UserManageMutation, InternshipMutation, graphene.ObjectType):
    pass

schema = graphene.Schema(query=Query, mutation=Mutation)