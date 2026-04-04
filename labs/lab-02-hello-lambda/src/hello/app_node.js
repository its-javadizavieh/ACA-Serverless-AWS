/**
 * Lab 02 – Hello Lambda (Node.js version)
 * Demonstrates the same concepts as the Python version.
 */

"use strict";

// Initialise outside handler for warm-start reuse
const greeting = process.env.GREETING || "Hello";
const moduleLoadedAt = Date.now();

exports.handler = async (event, context) => {
  console.log(JSON.stringify({
    action: "invocation_start",
    requestId: context.awsRequestId,
    functionName: context.functionName,
  }));

  const name = (event && event.name) ? event.name : "Lambda Learner";

  const body = {
    message: `${greeting}, ${name}! 👋`,
    requestId: context.awsRequestId,
    functionName: context.functionName,
    functionVersion: context.functionVersion,
    memoryLimitMB: context.memoryLimitInMB,
    remainingTimeMs: context.getRemainingTimeInMillis(),
    moduleAgeSeconds: ((Date.now() - moduleLoadedAt) / 1000).toFixed(3),
  };

  console.log(JSON.stringify({ action: "invocation_end", statusCode: 200 }));

  return {
    statusCode: 200,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  };
};
