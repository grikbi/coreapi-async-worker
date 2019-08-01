"""Implementation of the REST API for the backbone service."""

import os
import logging
import uvicorn
import json
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from models import ServiceInput
from recommender import RecommendationTask
from stack_aggregator import StackAggregator
from raven.contrib.flask import Sentry
from src.utils import push_data, total_time_elapsed, get_time_delta

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SENTRY_DSN = os.environ.get("SENTRY_DSN", "")
#sentry = Sentry(app, dsn=SENTRY_DSN, logging=True, level=logging.ERROR)


@app.get('/api/v1/readiness')
def readiness():
    """Handle GET requests that are sent to /api/v1/readiness REST API endpoint."""
    return {}


@app.get('/api/v1/liveness')
def liveness(request: Request):
    """Handle GET requests that are sent to /api/v1/liveness REST API endpoint."""
    request_dict = dict(request)
    metrics_payload = {
        'pid': os.getpid(),
        'hostname': os.environ.get("HOSTNAME"),
        'endpoint': request_dict['path'],
        'request_method': request_dict['method'],
        'status_code': 200
    }
    print (metrics_payload)
    return {}


@app.post('/api/v1/recommender')
def recommender(payload: ServiceInput, request: Request):
    """Handle POST requests that are sent to /api/v1/recommender REST API endpoint."""
    r = {'recommendation': 'failure', 'external_request_id': None}

    request_dict = dict(request)
    metrics_payload = {
        'pid': os.getpid(),
        'hostname': os.environ.get("HOSTNAME"),
        'endpoint': request_dict['path'],
        'request_method': request_dict['method'],
        'status_code': 200
    }

    input_json = json.loads(payload.json())
    app.logger.debug('recommender/ request with payload: {p}'.format(p=input_json))

    if input_json and 'external_request_id' in input_json and input_json['external_request_id']:
        try:
            check_license = request.args.get('check_license', 'false') == 'true'
            persist = request.args.get('persist', 'true') == 'true'
            r = RecommendationTask().execute(input_json, persist=persist,
                                             check_license=check_license)
        except Exception as e:
            r = {
                'recommendation': 'unexpected error',
                'external_request_id': input_json.get('external_request_id'),
                'message': '%s' % e
            }
            metrics_payload['status_code'] = 400

    try:
        metrics_payload['value'] = get_time_delta(audit_data=r['result']['_audit'])
        push_data(metrics_payload)
    except KeyError:
        pass

    return r, metrics_payload['status_code']


@app.post('/api/v1/stack_aggregator')
def stack_aggregator(payload: ServiceInput, request: Request):
    """Handle POST requests that are sent to /api/v1/stack_aggregator REST API endpoint."""
    s = {'stack_aggregator': 'failure', 'external_request_id': None}

    request_dict = dict(request)
    metrics_payload = {
        'pid': os.getpid(),
        'hostname': os.environ.get("HOSTNAME"),
        'endpoint': request_dict['path'],
        'request_method': request_dict['method'],
        'status_code': 200
    }

    input_json = json.loads(payload.json())
    if input_json and 'external_request_id' in input_json \
            and input_json['external_request_id']:

        try:
            persist = request.args.get('persist', 'true') == 'true'
            s = StackAggregator().execute(input_json, persist=persist)
            if s is not None and s.get('result') and s.get('result').get('_audit'):
                # Creating and Pushing Total Metrics Data to Accumulator
                metrics_payload['value'] = total_time_elapsed(
                    sa_audit_data=s['result']['_audit'],
                    external_request_id=input_json['external_request_id'])
                push_data(metrics_payload)

        except Exception as e:
            s = {
                'stack_aggregator': 'unexpected error',
                'external_request_id': input_json.get('external_request_id'),
                'message': '%s' % e
            }
            metrics_payload['status_code'] = 400

        try:
            # Pushing Individual Metrics Data to Accumulator
            metrics_payload['value'] = get_time_delta(audit_data=s['result']['_audit'])
            metrics_payload['endpoint'] = request.endpoint
            push_data(metrics_payload)
        except KeyError:
            pass

    return s


if __name__ == "__main__":
    app.run()
