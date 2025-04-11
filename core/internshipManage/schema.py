# import graphene
# from graphene_django.types import DjangoObjectType
# from graphene_django.filter import DjangoFilterConnectionField
# from .models import Internship, InternshipDiary, Evaulation

# class InternshipNode(DjangoObjectType):
#     class Meta:
#         model = Internship
#         fields = "__all__"
#         filter_fields = {
#             "id": ["exact"],
#             "student": ["exact"],
#             "company": ["exact"],
#             "start_date": ["exact", "gte", "lte"],
#             "end_date": ["exact", "gte", "lte"],
#             "position": ["exact", "icontains"],
#             "status": ["exact"],
#         }
#         interfaces = (graphene.relay.Node,)