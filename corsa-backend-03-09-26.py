#!/usr/bin/env python3
"""
Generate Corsa Backend architecture diagram
Usage: python corsa-backend-03-09-26.py
Requires: pip install diagrams
"""

from diagrams import Diagram, Cluster, Edge, Node
from diagrams.aws.general import User, Client
from diagrams.aws.integration import Appsync, EventbridgeScheduler
from diagrams.aws.compute import Lambda
from diagrams.aws.database import DynamodbTable
from diagrams.aws.storage import SimpleStorageServiceS3Bucket
from diagrams.aws.network import APIGateway, CloudFront
from diagrams.aws.management import SystemsManagerParameterStore


# Larger font sizes for better readability
CLUSTER_LABEL_ATTR = {
    "fontsize": "60",
    "labelfontsize": "60",
    "fontname": "Helvetica",
}

FONT_SIZE = "60"


def icon_with_label(icon_node: Node, text: str, *, fontsize: str = "72") -> Node:
    """
    Render the icon without a label, and render text as a separate plaintext node.
    This prevents label text from being drawn on top of the icon.
    """
    icon_node.label = ""

    label_node = Node(
        text,
        shape="plaintext",
        fontsize=fontsize,
    )

    # Invisible edge "attaches" the label to the icon in the layout.
    icon_node >> Edge(style="invis") >> label_node
    return icon_node


# Race-purse-like "horizontal slide" tuning
graph_attr = {
    "rankdir": "LR",
    "ratio": "fill",
    "size": "45,25!",  # slightly wider
    "pad": "0.45",
    "nodesep": "0.7",
    "ranksep": "0.7",
    "splines": "spline",
    "compound": "true",
    "newrank": "true",
    "fontsize": "72",
}

# Keep icon node labels off; text labels are separate plaintext nodes.
node_attr = {
    "fontsize": "36",
    "margin": "0",
    "width": "2.0",
    "height": "2.0",
    "fixedsize": "true",
    "imagescale": "true",
}

edge_attr = {
    "fontsize": "48",
    "arrowsize": "3.0",
    "penwidth": "2.5",
}

with Diagram(
    "Corsa Backend CDK Stack",
    direction="LR",
    show=False,
    filename="corsa_backend_architecture",
    graph_attr=graph_attr,
    node_attr=node_attr,
    edge_attr=edge_attr,
) as d:

    # External clients / systems
    web_client = icon_with_label(Client(""), "NextJS/Web Client\n(Corsa UI)")
    admin_client = icon_with_label(Client(""), "Admin/Utility\nClient")
    strava = icon_with_label(User(""), "Strava\n(External)")
    garmin = icon_with_label(User(""), "Garmin/InReach\n(External)")

    with Cluster("AWS Account", graph_attr=CLUSTER_LABEL_ATTR):
        with Cluster("Deployment Region", graph_attr=CLUSTER_LABEL_ATTR):
            with Cluster("Corsa Backend Stack", graph_attr=CLUSTER_LABEL_ATTR):

                appsync = icon_with_label(Appsync(""), "AWS AppSync GraphQL API\n(corsa-graphql-api)")
                api_gateway = icon_with_label(APIGateway(""), "Amazon API Gateway\n(CorsaUtilityApi)")

                with Cluster("GraphQL Resolvers", graph_attr=CLUSTER_LABEL_ATTR):
                    query_lambda = icon_with_label(Lambda(""), "QueryResolverLambda")
                    mutation_lambda = icon_with_label(Lambda(""), "MutationResolverLambda")
                    subscription_lambda = icon_with_label(Lambda(""), "SubscriptionLambda")

                with Cluster("API Gateway Handlers", graph_attr=CLUSTER_LABEL_ATTR):
                    strava_webhook = icon_with_label(Lambda(""), "StravaWebhookLambda")
                    inreach_webhook = icon_with_label(Lambda(""), "InreachWebhookLambda")
                    garmin_verify = icon_with_label(Lambda(""), "GarminVerifyLambda")
                    retrieve_points = icon_with_label(Lambda(""), "RetrievePointDataLambda")
                    new_user = icon_with_label(Lambda(""), "NewUserLambda")
                    init_route = icon_with_label(Lambda(""), "InitRouteUploadLambda")
                    firebase_auth = icon_with_label(Lambda(""), "FirebaseAuthorizerLambda")

                with Cluster("Scheduled Pollers", graph_attr=CLUSTER_LABEL_ATTR):
                    eventbridge_1 = icon_with_label(EventbridgeScheduler(""), "EventBridge\n(every 1 min)")
                    eventbridge_2 = icon_with_label(EventbridgeScheduler(""), "EventBridge\n(every 1 min)")
                    device_poller = icon_with_label(Lambda(""), "DeviceVerificationPollerLambda")
                    livestream_poller = icon_with_label(Lambda(""), "LiveStreamKmlPollerLambda")

                process_route = icon_with_label(Lambda(""), "ProcessRouteUploadLambda")

                with Cluster("DynamoDB Tables", graph_attr=CLUSTER_LABEL_ATTR):
                    users_table = icon_with_label(DynamodbTable(""), "UsersTable")
                    route_table = icon_with_label(DynamodbTable(""), "RouteTable")
                    device_table = icon_with_label(DynamodbTable(""), "DeviceTable")
                    points_table = icon_with_label(DynamodbTable(""), "PointsTable")
                    livestreams_table = icon_with_label(DynamodbTable(""), "LiveStreamsTable")
                    chat_table = icon_with_label(DynamodbTable(""), "ChatTable")
                    post_table = icon_with_label(DynamodbTable(""), "PostTable")

                with Cluster("Storage", graph_attr=CLUSTER_LABEL_ATTR):
                    geojson_bucket = icon_with_label(SimpleStorageServiceS3Bucket(""), "corsa-geojson-bucket")
                    general_bucket = icon_with_label(SimpleStorageServiceS3Bucket(""), "corsa-general-bucket")
                    user_images_bucket = icon_with_label(SimpleStorageServiceS3Bucket(""), "corsa-user-images")

                with Cluster("CDN", graph_attr=CLUSTER_LABEL_ATTR):
                    cloudfront = icon_with_label(CloudFront(""), "CloudFront\n(UserImagesDistribution)")

                with Cluster("Config / Secrets", graph_attr=CLUSTER_LABEL_ATTR):
                    param_store = icon_with_label(SystemsManagerParameterStore(""), "Parameter Store")

    #
    # Edges (flows)
    #

    # Web -> AppSync
    web_client >> Edge(label="GraphQL over HTTPS", fontsize=FONT_SIZE) >> appsync

    # AppSync -> resolvers
    appsync >> query_lambda
    appsync >> mutation_lambda
    appsync >> subscription_lambda

    # Resolvers -> DynamoDB
    query_lambda >> Edge(label="Read", fontsize=FONT_SIZE) >> users_table
    query_lambda >> Edge(label="Read", fontsize=FONT_SIZE) >> route_table
    query_lambda >> Edge(label="Read", fontsize=FONT_SIZE) >> device_table
    query_lambda >> Edge(label="Read", fontsize=FONT_SIZE) >> points_table

    mutation_lambda >> Edge(label="Read/Write", fontsize=FONT_SIZE) >> users_table
    mutation_lambda >> Edge(label="Read/Write", fontsize=FONT_SIZE) >> route_table
    mutation_lambda >> Edge(label="Read/Write", fontsize=FONT_SIZE) >> device_table
    mutation_lambda >> Edge(label="Read/Write", fontsize=FONT_SIZE) >> points_table
    # Added edges for post, chat, livestream tables
    mutation_lambda >> Edge(label="Read/Write", fontsize=FONT_SIZE) >> post_table
    mutation_lambda >> Edge(label="Read/Write", fontsize=FONT_SIZE) >> chat_table
    mutation_lambda >> Edge(label="Read/Write", fontsize=FONT_SIZE) >> livestreams_table

    subscription_lambda >> users_table
    subscription_lambda >> points_table

    # Mutation -> S3
    mutation_lambda >> Edge(label="Read/Write Objects", fontsize=FONT_SIZE) >> geojson_bucket
    mutation_lambda >> Edge(label="Read/Write Objects", fontsize=FONT_SIZE) >> general_bucket
    mutation_lambda >> Edge(label="Read/Write Objects", fontsize=FONT_SIZE) >> user_images_bucket

    # External -> API Gateway
    strava >> Edge(label="Webhook", fontsize=FONT_SIZE) >> api_gateway
    garmin >> Edge(label="Webhook", fontsize=FONT_SIZE) >> api_gateway
    admin_client >> Edge(label="Utility calls", fontsize=FONT_SIZE) >> api_gateway

    # API Gateway -> handlers
    api_gateway >> strava_webhook
    api_gateway >> inreach_webhook
    api_gateway >> garmin_verify
    api_gateway >> retrieve_points
    api_gateway >> new_user
    api_gateway >> init_route
    api_gateway >> firebase_auth

    # Handlers -> DynamoDB
    strava_webhook >> users_table
    inreach_webhook >> device_table
    new_user >> users_table
    init_route >> route_table

    # Firebase authorizer -> Parameter Store
    firebase_auth >> Edge(label="Read config", fontsize=FONT_SIZE) >> param_store

    # EventBridge -> pollers
    eventbridge_1 >> device_poller
    eventbridge_2 >> livestream_poller

    # Pollers -> DynamoDB + AppSync publish
    device_poller >> points_table
    livestream_poller >> points_table
    device_poller >> Edge(label="Publish waypoint", fontsize=FONT_SIZE) >> appsync
    livestream_poller >> Edge(label="Publish waypoint", fontsize=FONT_SIZE) >> appsync

    # S3 event trigger path
    geojson_bucket >> Edge(label="Object created", fontsize=FONT_SIZE) >> process_route
    process_route >> route_table
    process_route >> Edge(label="Write GeoJSON", fontsize=FONT_SIZE) >> geojson_bucket

    # CloudFront image delivery
    user_images_bucket >> cloudfront
    web_client >> Edge(label="Image delivery", fontsize=FONT_SIZE) >> cloudfront

    #
    # same-rank rows (horizontal legibility like your other diagrams)
    #
    d.dot.subgraph(
        name="rank_graphql_resolvers",
        graph_attr={"rank": "same"},
        body=[
            f"{query_lambda._id}",
            f"{mutation_lambda._id}",
            f"{subscription_lambda._id}",
        ],
    )
    d.dot.subgraph(
        name="rank_api_handlers",
        graph_attr={"rank": "same"},
        body=[
            f"{strava_webhook._id}",
            f"{inreach_webhook._id}",
            f"{garmin_verify._id}",
            f"{retrieve_points._id}",
            f"{new_user._id}",
            f"{init_route._id}",
            f"{firebase_auth._id}",
        ],
    )
    d.dot.subgraph(
        name="rank_tables",
        graph_attr={"rank": "same"},
        body=[
            f"{users_table._id}",
            f"{route_table._id}",
            f"{device_table._id}",
            f"{points_table._id}",
            f"{livestreams_table._id}",
            f"{chat_table._id}",
            f"{post_table._id}",
        ],
    )

print("Diagram generated: corsa_backend_architecture.png")