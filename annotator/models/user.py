# # -*- coding: utf-8 -*-
# import random
# import string
# from datetime import datetime

# from flask_login import UserMixin
# from flask_sqlalchemy import BaseQuery
# from sqlalchemy.ext.hybrid import hybrid_property
# from sqlalchemy.orm import relation
# from sqlalchemy_utils import (
#     EmailType,
#     LocaleType,
#     PasswordType,
#     TSVectorType,
#     UUIDType
# )

# from annotator.extensions import db

# from .organization import Organization


# class Dataset(db.Model):
#     __tablename__ = 'dataset'

#     id = db.Column(
#         UUIDType(binary=False),
#         server_default=db.func.uuid_generate_v4(),
#         primary_key=True
#     )

#     table_name = db.Column(
#         db.Unicode(255),
#         nullable=False,
#     )

#     free_text = db.Column(
#         db.Text(),
#         nullable=False
#     )

#     probability = db.Column(
#         db.Float(),
#         nullable=True
#     )

#     sort_value = db.Column(
#         db.Float(),
#         nullable=True
#     )
