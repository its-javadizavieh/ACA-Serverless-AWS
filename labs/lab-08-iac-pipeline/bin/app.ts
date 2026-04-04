#!/usr/bin/env node
import "source-map-support/register";
import * as cdk from "aws-cdk-lib";
import { ItemsApiStack } from "../lib/api-stack";

const app = new cdk.App();

const stageName = app.node.tryGetContext("stageName") ?? "dev";

new ItemsApiStack(app, "ItemsApiStack", {
  stageName,
  description: `Lab 08 – Items API (${stageName})`,
  tags: {
    Project: "ACA-Serverless-Course",
    Lab: "lab-08",
    Stage: stageName,
  },
});
