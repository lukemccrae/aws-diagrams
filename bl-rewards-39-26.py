#!/usr/bin/env python3
"""
Generate Burrito League Rewards architecture diagram
Usage: python bl-rewards-39-26.py
Requires: pip install diagrams
"""

from diagrams import Diagram, Cluster, Edge, Node
from diagrams.aws.general import User, Client
from diagrams.aws.integration import Appsync
from diagrams.aws.compute import Lambda
from diagrams.aws.database import DynamodbTable
from diagrams.aws.network import APIGateway


def icon_with_label(icon_node: Node, text: str, *, fontsize: str = "22") -> Node:
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


graph_attr = {
    "rankdir": "LR",
    "fontsize": "24",
    "pad": "1.5",
    "nodesep": "1.2",
    "ranksep": "1.5",
    "splines": "spline",
}

# Keep icon node labels off; text labels are separate plaintext nodes.
node_attr = {
    "fontsize": "1",
    "margin": "0",
}

edge_attr = {
    "fontsize": "18",
}

with Diagram(
    "Burrito League Rewards CDK Stack",
    direction="LR",
    show=False,
    filename="bl_rewards_architecture",
    graph_attr=graph_attr,
    node_attr=node_attr,
    edge_attr=edge_attr,
):
    # External clients / systems
    web_client = icon_with_label(Client(""), "NextJS/Web Client\n(Burrito League Rewards UI)")
    tremendous = icon_with_label(User(""), "Tremendous\n(External)")

    with Cluster("AWS Account"):
        with Cluster("Deployment Region"):
            with Cluster("Burrito League Rewards Stack"):
                appsync = icon_with_label(Appsync(""), "AWS AppSync GraphQL API\n(burrito-league-rewards)")
                api_gateway = icon_with_label(APIGateway(""), "Amazon API Gateway\n(burrito-league-rewards-api)")

                with Cluster("GraphQL Resolvers"):
                    query_lambda = icon_with_label(Lambda(""), "QueryResolverLambda")
                    mutation_lambda = icon_with_label(Lambda(""), "MutationResolverLambda")

                with Cluster("REST/API Handlers"):
                    redeem_lambda = icon_with_label(Lambda(""), "RedeemLambda")
                    webhook_lambda = icon_with_label(Lambda(""), "WebhookLambda")

                with Cluster("DynamoDB Tables"):
                    host_table = icon_with_label(DynamodbTable(""), "HostsTable")
                    token_table = icon_with_label(DynamodbTable(""), "RedemptionTokensTable")
                    redemption_table = icon_with_label(DynamodbTable(""), "RedemptionsTable")

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