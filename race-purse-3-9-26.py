#!/usr/bin/env python3
"""
Generate Race Purse (Endurance Pools) architecture diagram
Usage: python race-purse-3-9-26.py
Requires: pip install diagrams
"""

from diagrams import Diagram, Cluster, Edge, Node
from diagrams.aws.general import User, Client
from diagrams.aws.integration import Appsync
from diagrams.aws.compute import Lambda
from diagrams.aws.database import DynamodbTable
from diagrams.aws.network import APIGateway
from diagrams.aws.management import SystemsManagerParameterStore

CLUSTER_LABEL_ATTR = {
    "fontsize": "36",
    "labelfontsize": "36",
    "fontname": "Helvetica",
}

FONT_SIZE = "36"


def icon_with_label(icon_node: Node, text: str, *, fontsize: str = "48") -> Node:
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
    # Make it "slide-shaped" (Graphviz uses inches for size)
    "ratio": "fill",
    "size": "46,25!",
    "pad": "0.55",
    # Layout tuning: encourage horizontal spread, reduce vertical expansion
    "nodesep": "0.9",
    "ranksep": "0.8",
    "splines": "spline",
    "compound": "true",
    "newrank": "true",
    "fontsize": "48",
}

# Keep icon node labels off; text labels are separate plaintext nodes.
node_attr = {
    "fontsize": "15",
    "margin": "0",
    # make AWS service icons larger
    "width": "2.0",        # try 1.5–3.0
    "height": "2.0",
    "fixedsize": "true",   # forces the node to use width/height
    "imagescale": "true",  # scale the icon to the node size
}

edge_attr = {
    "fontsize": "28",
    "arrowsize": "3.0",   # default ~1.0; try 1.5–3.0
    "penwidth": "2.5",    # makes the edge line thicker
}

with Diagram(
    "Race Purse (Endurance Pools) CDK Stack",
    direction="LR",
    show=False,
    filename="endurance_pools_architecture",
    graph_attr=graph_attr,
    node_attr=node_attr,
    edge_attr=edge_attr,
) as d:
    # External clients / systems
    web_client = icon_with_label(Client(""), "NextJS/Web Client\n(Race Purse UI)")
    stripe = icon_with_label(User(""), "Stripe\n(External)")

    with Cluster("AWS Account", graph_attr=CLUSTER_LABEL_ATTR):
        with Cluster("Deployment Region", graph_attr=CLUSTER_LABEL_ATTR):
            with Cluster("Race Purse (Endurance Pools) Stack", graph_attr=CLUSTER_LABEL_ATTR):
                appsync = icon_with_label(Appsync(""), "AWS AppSync GraphQL API")
                api_gateway = icon_with_label(
                    APIGateway(""),
                    "Amazon API Gateway\n(RacePurseDonationAPI)",
                )

                with Cluster("GraphQL Resolvers", graph_attr=CLUSTER_LABEL_ATTR):
                    query_lambda = icon_with_label(Lambda(""), "QueryResolverLambda")
                    mutation_lambda = icon_with_label(Lambda(""), "MutationResolverLambda")

                with Cluster("REST/Payment Handlers", graph_attr=CLUSTER_LABEL_ATTR):
                    create_checkout = icon_with_label(
                        Lambda(""),
                        "StripeCreateCheckoutSessionLambda",
                    )
                    stripe_webhook = icon_with_label(Lambda(""), "StripeWebhookLambda")

                with Cluster("DynamoDB Tables", graph_attr=CLUSTER_LABEL_ATTR):
                    events_table = icon_with_label(
                        DynamodbTable(""),
                        "EndurancePools-EventTable",
                    )
                    donations_table = icon_with_label(
                        DynamodbTable(""),
                        "EndurancePools-DonationsTable",
                    )
                    tiers_table = icon_with_label(
                        DynamodbTable(""),
                        "EndurancePools-TiersTable",
                    )
                    emojis_table = icon_with_label(
                        DynamodbTable(""),
                        "EndurancePools-EmojisTable",
                    )

                with Cluster("Config / Secrets", graph_attr=CLUSTER_LABEL_ATTR):
                    param_store = icon_with_label(
                        SystemsManagerParameterStore(""),
                        "SSM Parameter Store",
                    )

    # NextJS -> GraphQL
    web_client >> Edge(label="GraphQL over HTTPS", fontsize=FONT_SIZE) >> appsync

    # GraphQL -> resolvers
    appsync >> query_lambda
    appsync >> mutation_lambda

    # QueryResolverLambda -> all four tables (reads)
    query_lambda >> Edge(label="Read", fontsize=FONT_SIZE) >> events_table
    query_lambda >> Edge(label="Read", fontsize=FONT_SIZE) >> donations_table
    query_lambda >> Edge(label="Read", fontsize=FONT_SIZE) >> tiers_table
    query_lambda >> Edge(label="Read", fontsize=FONT_SIZE) >> emojis_table

    # MutationResolverLambda -> all four tables (read/write)
    mutation_lambda >> Edge(label="Read/Write", fontsize=FONT_SIZE) >> events_table
    mutation_lambda >> Edge(label="Read/Write", fontsize=FONT_SIZE) >> donations_table
    mutation_lambda >> Edge(label="Read/Write", fontsize=FONT_SIZE) >> tiers_table
    mutation_lambda >> Edge(label="Read/Write", fontsize=FONT_SIZE) >> emojis_table

    # REST/Payments entrypoint
    web_client >> Edge(label="Donation API", fontsize=FONT_SIZE) >> api_gateway
    api_gateway >> create_checkout
    api_gateway >> stripe_webhook

    # Stripe checkout session flow
    create_checkout >> Edge(label="Checkout session", fontsize=FONT_SIZE) >> stripe
    stripe >> Edge(label="Webhook", fontsize=FONT_SIZE) >> api_gateway

    # SSM Parameter Store access (Stripe API key / webhook secret)
    create_checkout >> Edge(label="GetParameter", fontsize=FONT_SIZE) >> param_store
    stripe_webhook >> Edge(label="GetParameter", fontsize=FONT_SIZE) >> param_store

    # StripeWebhookLambda -> Events + Donations tables (read/write per CDK grants)
    stripe_webhook >> Edge(label="Read/Write", fontsize=FONT_SIZE) >> events_table
    stripe_webhook >> Edge(label="Read/Write", fontsize=FONT_SIZE) >> donations_table

    # same-rank rows (key for horizontal legibility)
    d.dot.subgraph(
        name="rank_resolvers",
        graph_attr={"rank": "same"},
        body=[f"{query_lambda._id}", f"{mutation_lambda._id}"],
    )
    d.dot.subgraph(
        name="rank_payment_lambdas",
        graph_attr={"rank": "same"},
        body=[f"{create_checkout._id}", f"{stripe_webhook._id}"],
    )
    d.dot.subgraph(
        name="rank_tables",
        graph_attr={"rank": "same"},
        body=[
            f"{events_table._id}",
            f"{donations_table._id}",
            f"{tiers_table._id}",
            f"{emojis_table._id}",
        ],
    )

print("Diagram generated: endurance_pools_architecture.png")