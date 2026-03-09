#!/usr/bin/env python3
"""
Generate Corsa Backend architecture diagram
Usage: python generate_diagram.py
Requires: pip install diagrams
"""

from diagrams import Diagram, Cluster, Edge
from diagrams.aws.general import User, Client
from diagrams.aws.integration import Appsync, EventbridgeScheduler
from diagrams.aws.compute import Lambda
from diagrams.aws.database import DynamodbTable
from diagrams.aws.storage import SimpleStorageServiceS3Bucket
from diagrams.aws.network import APIGateway, CloudFront
from diagrams.aws.management import SystemsManagerParameterStore

with Diagram("Corsa Backend CDK Stack", direction="LR", show=False, filename="corsa_backend_architecture2"):
    
    # External clients
    web_client = Client("NextJS/Web Client\n(Corsa UI)")
    strava = User("Strava\n(External)")
    garmin = User("Garmin/InReach\n(External)")
    admin_client = Client("Admin/Utility\nClient")
    
    with Cluster("AWS Account"):
        with Cluster("Deployment Region"):
            with Cluster("Corsa Backend Stack"):
                
                appsync = Appsync("AWS AppSync GraphQL API\n(corsa-graphql-api)")
                api_gateway = APIGateway("Amazon API Gateway\n(CorsaUtilityApi)")
                
                with Cluster("GraphQL Resolvers"):
                    query_lambda = Lambda("QueryResolverLambda")
                    mutation_lambda = Lambda("MutationResolverLambda")
                    subscription_lambda = Lambda("subscriptionLambda")
                
                with Cluster("API Gateway Handlers"):
                    strava_webhook = Lambda("StravaWebhookLambda")
                    inreach_webhook = Lambda("InreachWebhookLambda")
                    garmin_verify = Lambda("GarminVerifyLambda")
                    retrieve_points = Lambda("RetrievePointDataLambda")
                    new_user = Lambda("newUserLambda")
                    init_route = Lambda("initRouteUploadLambda")
                    firebase_auth = Lambda("firebaseAuthorizerLambda")
                
                with Cluster("Scheduled Pollers"):
                    eventbridge_1 = EventbridgeScheduler("EventBridge\n(every 1 min)")
                    eventbridge_2 = EventbridgeScheduler("EventBridge\n(every 1 min)")
                    device_poller = Lambda("DeviceVerificationPollerLambda")
                    livestream_poller = Lambda("LiveStreamKmlPollerLambda")
                
                process_route = Lambda("processRouteUploadLambda")
                
                with Cluster("DynamoDB Tables"):
                    users_table = DynamodbTable("UsersTable")
                    route_table = DynamodbTable("RouteTable")
                    device_table = DynamodbTable("DeviceTable")
                    points_table = DynamodbTable("PointsTable")
                    livestreams_table = DynamodbTable("LiveStreamsTable")
                    chat_table = DynamodbTable("ChatTable")
                    post_table = DynamodbTable("PostTable")
                
                geojson_bucket = SimpleStorageServiceS3Bucket("corsa-geojson-bucket")
                general_bucket = SimpleStorageServiceS3Bucket("corsa-general-bucket")
                user_images_bucket = SimpleStorageServiceS3Bucket("corsa-user-images")
                
                cloudfront = CloudFront("CloudFront\n(UserImagesDistribution)")
                param_store = SystemsManagerParameterStore("Parameter Store")
    
    # External to AppSync
    web_client >> Edge(label="GraphQL over HTTPS") >> appsync
    
    # AppSync to resolvers
    appsync >> query_lambda
    appsync >> mutation_lambda
    appsync >> subscription_lambda
    
    # Resolvers to DynamoDB
    query_lambda >> Edge(label="Read") >> users_table
    query_lambda >> route_table
    query_lambda >> device_table
    query_lambda >> points_table
    
    mutation_lambda >> Edge(label="Read/Write") >> users_table
    mutation_lambda >> route_table
    mutation_lambda >> device_table
    mutation_lambda >> points_table
    
    subscription_lambda >> users_table
    subscription_lambda >> points_table
    
    # Mutation Lambda to S3
    mutation_lambda >> Edge(label="Read/Write Objects") >> geojson_bucket
    mutation_lambda >> general_bucket
    mutation_lambda >> user_images_bucket
    
    # External to API Gateway
    strava >> Edge(label="Webhook") >> api_gateway
    garmin >> Edge(label="Webhook") >> api_gateway
    admin_client >> Edge(label="Utility calls") >> api_gateway
    
    # API Gateway to handlers
    api_gateway >> strava_webhook
    api_gateway >> inreach_webhook
    api_gateway >> garmin_verify
    api_gateway >> retrieve_points
    api_gateway >> new_user
    api_gateway >> init_route
    api_gateway >> firebase_auth
    
    # Handlers to DynamoDB
    strava_webhook >> users_table
    inreach_webhook >> device_table
    new_user >> users_table
    init_route >> route_table
    
    # Firebase authorizer to Parameter Store
    firebase_auth >> Edge(label="Read config") >> param_store
    
    # EventBridge to pollers
    eventbridge_1 >> device_poller
    eventbridge_2 >> livestream_poller
    
    # Pollers to DynamoDB and AppSync
    device_poller >> points_table
    livestream_poller >> points_table
    device_poller >> Edge(label="Publish waypoint") >> appsync
    livestream_poller >> Edge(label="Publish waypoint") >> appsync
    
    # S3 event trigger
    geojson_bucket >> Edge(label="Object created") >> process_route
    process_route >> route_table
    process_route >> Edge(label="Write GeoJSON") >> geojson_bucket
    
    # CloudFront
    user_images_bucket >> cloudfront
    web_client >> Edge(label="Image delivery") >> cloudfront

print("Diagram generated: corsa_backend_architecture2.png")
