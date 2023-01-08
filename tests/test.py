# import config
# import common
# # x = config.QueryRoot()
# # y = config.Collection()
# # y.id = ''
# # pp = config.ProductConnection()
# # pp.pageInfo = ''
# # y.products(pp,first=1)
# # x.collection(y, id="1232")
# # print(config.parse_gql_config(x))
# query = config.QueryRoot()

# con = config.Collection()
# con.handle = ''
# con.hasProduct('', id=1)
# query.collection(con, id='"gid://collection/001"')
# app = config.App()
# app.apiKey = ''
# query.appByHandle(app, handle='XXX')

# print(common.parse_gql_config(query))

# mu = config.Mutation()
# x = config.CollectionReorderProductsPayload()
# x.job.id = ''
# x.userErrors.field = ''
# x.userErrors.message = ''

# m1 = config.MoveInput()
# m1.id='"1111"'
# m1.newPosition='"0"'
# mu.collectionReorderProducts(x, id='"gid://collection/001"', moves=[m1])
# print(common.parse_gql_config(mu))