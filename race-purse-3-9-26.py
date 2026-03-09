#!/usr/bin/env python3
"""
Generate Endurance Pools architecture diagram
Usage: python generate_endurance_pools_diagram.py
Requires: pip install diagrams
"""

from diagrams import Diagram, Cluster, Edge
from diagrams.aws.general import User, Client
from diagrams.aws.integration import Appsync
from diagrams.aws.compute import Lambda
from diagrams.aws.database import DynamodbTable
from diagrams.aws.network import APIGateway
from diagrams.aws.management import SystemsManagerParameterStore

graph_attr = {
    "rankdir": "LR",
    "fontsize": "24",
    "pad": "1.5",
    "nodesep": "1.2",
    "ranksep": "1.5",
    "splines": "spline",
}

node_attr = {
    "fontsize": "18",
    "margin": "0",
}

edge_attr = {
    "fontsize": "16",
}

with Diagram(
    "Endurance Pools CDK Stack",
    show=False,
    filename="endurance_pools_architecture",
    graph_attr=graph_attr,
    node_attr=node_attr,
    edge_attr=edge_attr,
):

    # External clients / systems
    web_client = Client("NextJS/Web Client\n(Race Purse UI)")
    stripe = User("Stripe\n(External)")

    with Cluster("AWS Account"):

        with Cluster("Deployment Region"):

            with Cluster("Endurance Pools Stack"):

                appsync = Appsync("AWS AppSync\nGraphQL API")
                api_gateway = APIGateway("Amazon API Gateway\nRacePurseDonationAPI")

                with Cluster("GraphQL Resolvers"):

                    query_lambda = Lambda("QueryResolverLambda")
                    mutation_lambda = Lambda("MutationResolverLambda")

                with Cluster("Payment Handlers"):

                    create_checkout = Lambda("StripeCreateCheckoutSessionLambda")
                    stripe_webhook = Lambda("StripeWebhookLambda")

                with Cluster("DynamoDB Tables"):

                    events_table = DynamodbTable("EventTable")
                    donations_table = DynamodbTable("DonationsTable")
                    tiers_table = DynamodbTable("TiersTable")
                    emojis_table = DynamodbTable("EmojisTable")

                param_store = SystemsManagerParameterStore("Parameter Store")

    # NextJS -> GraphQL
    web_client >> Edge(label="GraphQL over HTTPS") >> appsync

    # GraphQL -> resolver lambdas
    appsync >> query_lambda
    appsync >> mutation_lambda

    # Resolvers -> DynamoDB
    query_lambda >> Edge(label="Read") >> events_table
    query_lambda >> donations_table
    query_lambda >> tiers_table
    query_lambda >> emojis_table

    mutation_lambda >> Edge(label="Read/Write") >> events_table
    mutation_lambda >> donations_table
    mutation_lambda >> tiers_table
    mutation_lambda >> emojis_table

    # NextJS -> API Gateway
    web_client >> Edge(label="Payments API") >> api_gateway

    # API Gateway -> payment lambdas
    api_gateway >> create_checkout
    api_gateway >> stripe_webhook

    # Stripe interactions
    create_checkout >> Edge(label="Create Checkout Session") >> stripe
    stripe >> Edge(label="Webhook Events") >> api_gateway

    # Parameter Store reads
    create_checkout >> Edge(label="Read config/secret values") >> param_store
    stripe_webhook >> Edge(label="Read config/secret values") >> param_store

print("Diagram generated: endurance_pools_architecture.png")