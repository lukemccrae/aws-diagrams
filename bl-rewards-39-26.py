#!/usr/bin/env python3
"""
Generate Burrito League Rewards architecture diagram
Usage: python generate_bl_rewards_diagram.py
Requires: pip install diagrams
"""

from diagrams import Diagram, Cluster, Edge
from diagrams.aws.general import User, Client
from diagrams.aws.integration import Appsync
from diagrams.aws.compute import Lambda
from diagrams.aws.database import DynamodbTable
from diagrams.aws.network import APIGateway

with Diagram(
    "Burrito League Rewards CDK Stack",
    direction="LR",
    show=False,
    filename="bl_rewards_architecture",
):
    # External clients / systems
    web_client = Client("NextJS/Web Client\n(Burrito League Rewards UI)")
    tremendous = User("Tremendous\n(External)")

    with Cluster("AWS Account"):
        with Cluster("Deployment Region"):
            with Cluster("Burrito League Rewards Stack"):
                appsync = Appsync("AWS AppSync GraphQL API\n(burrito-league-rewards)")
                api_gateway = APIGateway("Amazon API Gateway\n(burrito-league-rewards-api)")

                with Cluster("GraphQL Resolvers"):
                    query_lambda = Lambda("QueryResolverLambda")
                    mutation_lambda = Lambda("MutationResolverLambda")

                with Cluster("REST/API Handlers"):
                    redeem_lambda = Lambda("RedeemLambda")
                    webhook_lambda = Lambda("WebhookLambda")

                with Cluster("DynamoDB Tables"):
                    host_table = DynamodbTable("HostsTable")
                    token_table = DynamodbTable("RedemptionTokensTable")
                    redemption_table = DynamodbTable("RedemptionsTable")

    # NextJS -> GraphQL
    web_client >> Edge(label="GraphQL over HTTPS") >> appsync

    # GraphQL -> resolvers
    appsync >> query_lambda
    appsync >> mutation_lambda

    # Resolvers -> DynamoDB (simplified)
    query_lambda >> Edge(label="Read") >> host_table
    query_lambda >> token_table
    query_lambda >> redemption_table

    mutation_lambda >> Edge(label="Read/Write") >> host_table
    mutation_lambda >> token_table
    mutation_lambda >> redemption_table

    # Optional/parallel REST entrypoint (redeem flow, webhooks, etc.)
    web_client >> Edge(label="Redeem / Utility API") >> api_gateway
    api_gateway >> redeem_lambda
    api_gateway >> webhook_lambda

    redeem_lambda >> Edge(label="Read/Write") >> token_table
    redeem_lambda >> redemption_table

    webhook_lambda >> Edge(label="Read/Write") >> redemption_table

    # External rewards provider
    redeem_lambda >> Edge(label="Send reward / fulfillment") >> tremendous

print("Diagram generated: bl_rewards_architecture.png")