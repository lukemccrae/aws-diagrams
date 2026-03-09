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
from diagrams.aws.storage import SimpleStorageServiceS3Bucket
from diagrams.aws.management import SystemsManagerParameterStore


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
}

edge_attr = {
    "fontsize": "28",
}

with Diagram(
    "Burrito League Rewards CDK Stack",
    direction="LR",
    show=False,
    filename="bl_rewards_architecture",
    graph_attr=graph_attr,
    node_attr=node_attr,
    edge_attr=edge_attr,
) as d:
    # External clients / systems
    web_client = icon_with_label(Client(""), "NextJS/Web Client\n(Burrito League Rewards UI)")
    tremendous = icon_with_label(User(""), "Tremendous\n(External)")

    with Cluster("AWS Account"):
        with Cluster("Deployment Region"):
            with Cluster("Burrito League Rewards Stack"):
                appsync = icon_with_label(Appsync(""), "AWS AppSync GraphQL API")
                api_gateway = icon_with_label(
                    APIGateway(""),
                    "Amazon API Gateway",
                )

                with Cluster("GraphQL Resolvers"):
                    query_lambda = icon_with_label(Lambda(""), "QueryResolverLambda")
                    mutation_lambda = icon_with_label(Lambda(""), "MutationResolverLambda")

                with Cluster("REST/API Handlers"):
                    redeem_lambda = icon_with_label(Lambda(""), "RedeemRewardLambda")
                    # Note: CDK stack doesn’t define a webhook lambda right now, but keep if you still use it:
                    webhook_lambda = icon_with_label(Lambda(""), "WebhookLambda")

                with Cluster("DynamoDB Tables"):
                    runners_table = icon_with_label(DynamodbTable(""), "RunnersTable")
                    hosts_table = icon_with_label(DynamodbTable(""), "HostsTable")
                    rewards_table = icon_with_label(DynamodbTable(""), "RewardsTable")
                    redemption_requests_table = icon_with_label(
                        DynamodbTable(""),
                        "RedemptionsTable",
                    )

                with Cluster("Storage"):
                    proof_bucket = icon_with_label(
                        SimpleStorageServiceS3Bucket(""),
                        "ProofOfWorkBucket",
                    )

                with Cluster("Config / Secrets"):
                    param_store = icon_with_label(
                        SystemsManagerParameterStore(""),
                        "SSM Secret Store",
                    )

    # NextJS -> GraphQL
    web_client >> Edge(label="GraphQL over HTTPS") >> appsync

    # GraphQL -> resolvers
    appsync >> query_lambda
    appsync >> mutation_lambda

    # Resolvers -> DynamoDB (based on env vars + grants)
    query_lambda >> Edge(label="Read") >> runners_table
    query_lambda >> hosts_table
    query_lambda >> rewards_table

    mutation_lambda >> Edge(label="Read/Write") >> runners_table
    mutation_lambda >> hosts_table
    mutation_lambda >> rewards_table
    mutation_lambda >> redemption_requests_table

    # Mutation lambda reads from S3 bucket + reads SSM parameters (per CDK grants/policies)
    mutation_lambda >> Edge(label="Read objects") >> proof_bucket
    mutation_lambda >> Edge(label="GetParameter") >> param_store

    # REST entrypoint
    web_client >> Edge(label="Redeem API") >> api_gateway
    api_gateway >> redeem_lambda
    api_gateway >> webhook_lambda

    # Redeem lambda accesses DynamoDB + SSM + Tremendous
    redeem_lambda >> Edge(label="Read/Write") >> redemption_requests_table
    redeem_lambda >> runners_table
    redeem_lambda >> rewards_table
    redeem_lambda >> Edge(label="GetParameter") >> param_store
    redeem_lambda >> Edge(label="Send reward / fulfillment") >> tremendous

    # same-rank rows (key for horizontal legibility)
    d.dot.subgraph(
        name="rank_resolvers",
        graph_attr={"rank": "same"},
        body=[f"{query_lambda._id}", f"{mutation_lambda._id}"],
    )
    d.dot.subgraph(
        name="rank_rest",
        graph_attr={"rank": "same"},
        body=[f"{redeem_lambda._id}", f"{webhook_lambda._id}"],
    )
    d.dot.subgraph(
        name="rank_tables",
        graph_attr={"rank": "same"},
        body=[
            f"{runners_table._id}",
            f"{hosts_table._id}",
            f"{rewards_table._id}",
            f"{redemption_requests_table._id}",
        ],
    )

print("Diagram generated: bl_rewards_architecture.png")