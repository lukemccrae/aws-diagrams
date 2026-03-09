#!/usr/bin/env python3
"""
Generate Race Purse architecture diagram
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


def icon_with_label(icon_node: Node, text: str, *, fontsize: str = "48") -> Node:
    # Prevent icon labels from overlapping the icon itself; render text as a separate node
    icon_node.label = ""
    label_node = Node(text, shape="plaintext", fontsize=fontsize)

    # Invisible edge "attaches" the label to the icon while keeping it on blank canvas space
    icon_node >> Edge(style="invis") >> label_node
    return icon_node


graph_attr = {
    "rankdir": "LR",

    # Make it "slide-shaped" (Graphviz uses inches for size)
    # 13.333 x 7.5 == 16:9 at 96 DPI-ish thinking for PPT widescreen
    "ratio": "fill",
    "size": "22,15!",
    "pad": "0.15",

    # Layout tuning: encourage horizontal spread, reduce vertical expansion
    "nodesep": "0.9",
    "ranksep": "0.8",

    "splines": "spline",
    "compound": "true",
    "newrank": "true",
    "fontsize": "48",
}

# Icon nodes themselves should have effectively no label (we use plaintext label nodes)
node_attr = {"fontsize": "15", "margin": "0"}

# Edge label readability
edge_attr = {"fontsize": "28"}

with Diagram(
    "Race Purse CDK Stack",
    direction="LR",
    show=False,
    filename="endurance_pools_architecture",
    graph_attr=graph_attr,
    node_attr=node_attr,
    edge_attr=edge_attr,
    # optional: if you have a lot of crossings, DOT is usually best for "architecture" diagrams
    # graph_attr already implies DOT, but leaving explicit controls to Graphviz
) as d:
    web_client = icon_with_label(Client(""), "NextJS Web Client\n(Race Purse UI)")
    stripe = icon_with_label(User(""), "Stripe\n(External)")

    with Cluster("AWS Account"):
        with Cluster("Deployment Region"):
            with Cluster("Race Purse Stack"):
                appsync = icon_with_label(Appsync(""), "AWS AppSync\nGraphQL API")
                api_gateway = icon_with_label(APIGateway(""), "API Gateway\n(Donation API)")

                with Cluster("GraphQL Resolvers"):
                    query_lambda = icon_with_label(Lambda(""), "Query\nResolver")
                    mutation_lambda = icon_with_label(Lambda(""), "Mutation\nResolver")

                with Cluster("Payment Handlers"):
                    create_checkout = icon_with_label(Lambda(""), "Create\nCheckout")
                    stripe_webhook = icon_with_label(Lambda(""), "Stripe\nWebhook")

                with Cluster("DynamoDB Tables"):
                    events_table = icon_with_label(DynamodbTable(""), "Events")
                    donations_table = icon_with_label(DynamodbTable(""), "Donations")
                    tiers_table = icon_with_label(DynamodbTable(""), "Tiers")
                    emojis_table = icon_with_label(DynamodbTable(""), "Emojis")

                param_store = icon_with_label(SystemsManagerParameterStore(""), "Parameter\nStore")

    # Flows
    web_client >> Edge(label="GraphQL") >> appsync
    appsync >> query_lambda
    appsync >> mutation_lambda

    query_lambda >> Edge(label="Read") >> events_table
    query_lambda >> donations_table
    query_lambda >> tiers_table
    query_lambda >> emojis_table

    mutation_lambda >> Edge(label="Read/Write") >> events_table
    mutation_lambda >> donations_table
    mutation_lambda >> tiers_table
    mutation_lambda >> emojis_table

    web_client >> Edge(label="Payments") >> api_gateway
    api_gateway >> create_checkout
    api_gateway >> stripe_webhook

    create_checkout >> Edge(label="Checkout session") >> stripe
    stripe >> Edge(label="Webhook") >> api_gateway

    create_checkout >> Edge(label="Read") >> param_store
    stripe_webhook >> Edge(label="Read") >> param_store

    # same-rank rows (key for horizontal legibility)
    d.dot.subgraph(
        name="rank_resolvers",
        graph_attr={"rank": "same"},
        body=[f"{query_lambda._id}", f"{mutation_lambda._id}"],
    )
    d.dot.subgraph(
        name="rank_payments",
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