# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# coding: utf-8

"""
    Submarine Experiment API

    The Submarine REST API allows you to create, list, and get experiments. The API is hosted under the /v1/experiment route on the Submarine server. For example, to list experiments on a server hosted at http://localhost:8080, access http://localhost:8080/api/v1/experiment/  # noqa: E501

    The version of the OpenAPI document: 0.4.0
    Contact: dev@submarine.apache.org
    Generated by: https://openapi-generator.tech
"""


import pprint
import re  # noqa: F401

import six

from submarine.experiment.configuration import Configuration


class ExperimentSpec(object):
    """NOTE: This class is auto generated by OpenAPI Generator.
    Ref: https://openapi-generator.tech

    Do not edit the class manually.
    """

    """
    Attributes:
      openapi_types (dict): The key is attribute name
                            and the value is attribute type.
      attribute_map (dict): The key is attribute name
                            and the value is json key in definition.
    """
    openapi_types = {
        'meta': 'ExperimentMeta',
        'environment': 'Environment',
        'spec': 'dict(str, ExperimentTaskSpec)'
    }

    attribute_map = {
        'meta': 'meta',
        'environment': 'environment',
        'spec': 'spec'
    }

    def __init__(self, meta=None, environment=None, spec=None, local_vars_configuration=None):  # noqa: E501
        """ExperimentSpec - a model defined in OpenAPI"""  # noqa: E501
        if local_vars_configuration is None:
            local_vars_configuration = Configuration()
        self.local_vars_configuration = local_vars_configuration

        self._meta = None
        self._environment = None
        self._spec = None
        self.discriminator = None

        if meta is not None:
            self.meta = meta
        if environment is not None:
            self.environment = environment
        if spec is not None:
            self.spec = spec

    @property
    def meta(self):
        """Gets the meta of this ExperimentSpec.  # noqa: E501


        :return: The meta of this ExperimentSpec.  # noqa: E501
        :rtype: ExperimentMeta
        """
        return self._meta

    @meta.setter
    def meta(self, meta):
        """Sets the meta of this ExperimentSpec.


        :param meta: The meta of this ExperimentSpec.  # noqa: E501
        :type: ExperimentMeta
        """

        self._meta = meta

    @property
    def environment(self):
        """Gets the environment of this ExperimentSpec.  # noqa: E501


        :return: The environment of this ExperimentSpec.  # noqa: E501
        :rtype: Environment
        """
        return self._environment

    @environment.setter
    def environment(self, environment):
        """Sets the environment of this ExperimentSpec.


        :param environment: The environment of this ExperimentSpec.  # noqa: E501
        :type: Environment
        """

        self._environment = environment

    @property
    def spec(self):
        """Gets the spec of this ExperimentSpec.  # noqa: E501


        :return: The spec of this ExperimentSpec.  # noqa: E501
        :rtype: dict(str, ExperimentTaskSpec)
        """
        return self._spec

    @spec.setter
    def spec(self, spec):
        """Sets the spec of this ExperimentSpec.


        :param spec: The spec of this ExperimentSpec.  # noqa: E501
        :type: dict(str, ExperimentTaskSpec)
        """

        self._spec = spec

    def to_dict(self):
        """Returns the model properties as a dict"""
        result = {}

        for attr, _ in six.iteritems(self.openapi_types):
            value = getattr(self, attr)
            if isinstance(value, list):
                result[attr] = list(map(
                    lambda x: x.to_dict() if hasattr(x, "to_dict") else x,
                    value
                ))
            elif hasattr(value, "to_dict"):
                result[attr] = value.to_dict()
            elif isinstance(value, dict):
                result[attr] = dict(map(
                    lambda item: (item[0], item[1].to_dict())
                    if hasattr(item[1], "to_dict") else item,
                    value.items()
                ))
            else:
                result[attr] = value

        return result

    def to_str(self):
        """Returns the string representation of the model"""
        return pprint.pformat(self.to_dict())

    def __repr__(self):
        """For `print` and `pprint`"""
        return self.to_str()

    def __eq__(self, other):
        """Returns true if both objects are equal"""
        if not isinstance(other, ExperimentSpec):
            return False

        return self.to_dict() == other.to_dict()

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        if not isinstance(other, ExperimentSpec):
            return True

        return self.to_dict() != other.to_dict()
