import jwt
from django.conf import settings
from account.models import UserToken
from .notification import send_notification
from .utils_consumers import ActiveUsers as au

async def check_authorization_header(self):
	print("In check_auth function!!!")
	# Extract JWT token from the Authorization header
	#Retrieve Authorization header from headers
	#Decodes the bytes obj value of the "Authorization" header into a UTF-8 str
	#converts the binary data into a human-readable string
	#b"" used to present byte literal, http headers name typically present as byte obj rather than str
	headers = self.scope.get("headers")
	authorization_header = None
	authFlag = False
	for header_name, header_value in headers:
		if header_name == b"authorization":
			authFlag = True
			authorization_header = header_value.decode("utf-8")
			break
	if authFlag is False:
		return
	#Split value of Authorization header by space Bearer and token part
	#_ is placeholder for Bearer => not use anymore so discard it
	#jwt_token for token part
	try:
		bearer, jwt_token = authorization_header.split(" ")
	except ValueError:
		await self.ft_send_err("disconnect", "Invalid Authorization header for jwt")
		# return JsonResponse({"details": "Invalid authorization header format: Bearer token is missing"}, status=400)

	if bearer.lower() != "bearer":
		print("Wrong type of authorization header, it should be Bearer")
		await self.ft_send_err("disconnect", "Wrong type of authorization header: should be Bearer!!!")
		return

	if not jwt_token:
		# No token provided, close the connection
		print("No JWT token provided!!!")
		await self.ft_send_err("disconnect", "No JWT token provided!!!")
		return

	try:
		# Decode and verify the JWT token
		#decode_token with have key value as follow
		#sub: subject present user id
		#name: username
		#iat: issue at => time token was issued
		#exp: expiration time in unix time
		decoded_token = jwt.decode(jwt_token, settings.JWT_KEY, algorithms=["HS256"])
	except jwt.ExpiredSignatureError:
		# Token has expired, close the connection
		print("JWT token has expired!!!")
		await self.ft_send_err("disconnect", "JWT token has expired!!!")
	except jwt.InvalidTokenError:
		# Invalid token, close the connection
		print("Invalid JWT token!!!")
		await self.ft_send_err("disconnect", "Invalid JWT token!!!")
		return

	# Extract user ID from the decoded token
	user_id = decoded_token["name"]
	self.user = user_id

	if not self.user:
		print("User is invalid!!!")
		await self.ft_send_err("disconnect", "User is invalid!!!")
		return

	# await send_notification(self, self.user)
	print(f"Connect from user_id: {self.user}")

async def check_authorization_payload(self):
	print("In check auth payload!!!")
	if self.user:
		pass
	elif authorization := self.data.get("authorization"):
		self.user = await check_jwt(self, authorization)
		if self.user:
			# await send_notification(self, self.user)
			print("After send noti")
	else:
		print("Invalid authentication!!!")
		await self.ft_send_err("disconnect", "Invalid registration. Closing connection.")
		raise self.CustomException("Unauthorized")

async def check_jwt(self, token):
	print("Check jwt!!!")
	token = (
		await UserToken.objects.filter(access_token=token)
		.select_related("user")
		.afirst()
	)
	if not token or not token.is_token_valid():
		print("Token is invalid!!!!")
		await self.ft_send_err("disconnect", "Unauthorized, invalid token. Closing connection.")
		raise self.CustomException("Unauthorized")
	else:
		print("Pass auth")
		return token.user.username
