# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements. See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest
from datetime import datetime
from typing import List

import freezegun
import pytest
from freezegun import freeze_time

import submarine
from submarine.entities.model_registry import ModelVersion, RegisteredModel
from submarine.entities.model_registry.model_stages import (
    STAGE_ARCHIVED,
    STAGE_DEVELOPING,
    STAGE_NONE,
    STAGE_PRODUCTION,
)
from submarine.exceptions import SubmarineException
from submarine.store.database import models
from submarine.store.model_registry.sqlalchemy_store import SqlAlchemyStore

freezegun.configure(default_ignore_list=["threading", "tensorflow"])


@pytest.mark.e2e
class TestSqlAlchemyStore(unittest.TestCase):
    def setUp(self):
        submarine.set_db_uri("mysql+pymysql://submarine_test:password_test@localhost:3306/submarine_test")
        self.db_uri = submarine.get_db_uri()
        self.store = SqlAlchemyStore(self.db_uri)

    def tearDown(self):
        submarine.set_db_uri(None)
        models.Base.metadata.drop_all(self.store.engine)

    def test_create_registered_model(self):
        name1 = "test_create_RM_1"
        rm1 = self.store.create_registered_model(name1)
        self.assertEqual(rm1.name, name1)
        self.assertEqual(rm1.description, None)

        # error in duplicate
        with self.assertRaises(SubmarineException):
            self.store.create_registered_model(name1)

        # test create with tags
        name2 = "test_create_RM_2"
        tags = ["tag1", "tag2"]
        rm2 = self.store.create_registered_model(name2, tags=tags)
        rm2d = self.store.get_registered_model(name2)
        self.assertEqual(rm2.name, name2)
        self.assertEqual(rm2.tags, tags)
        self.assertEqual(rm2d.name, name2)
        self.assertEqual(rm2d.tags, tags)

        # test create with description
        name3 = "test_create_RM_3"
        description = "A test description."
        rm3 = self.store.create_registered_model(name3, description)
        rm3d = self.store.get_registered_model(name3)
        self.assertEqual(rm3.name, name3)
        self.assertEqual(rm3.description, description)
        self.assertEqual(rm3d.name, name3)
        self.assertEqual(rm3d.description, description)

        # invalid model name
        with self.assertRaises(SubmarineException):
            self.store.create_registered_model(None)
        with self.assertRaises(SubmarineException):
            self.store.create_registered_model("")

    def test_update_registered_model_description(self):
        name = "test_update_RM"
        rm1 = self.store.create_registered_model(name)
        rm1d = self.store.get_registered_model(name)
        self.assertEqual(rm1.name, name)
        self.assertEqual(rm1d.description, None)

        # update description
        fake_datetime = datetime.strptime("2021-11-11 11:11:11.111000", "%Y-%m-%d %H:%M:%S.%f")
        with freeze_time(fake_datetime):
            rm2 = self.store.update_registered_model_description(name, "New description.")
            rm2d = self.store.get_registered_model(name)
            self.assertEqual(rm2.name, name)
            self.assertEqual(rm2.description, "New description.")
            self.assertEqual(rm2d.name, name)
            self.assertEqual(rm2d.description, "New description.")
            self.assertEqual(rm2d.last_updated_time, fake_datetime)

    def test_rename_registered_model(self):
        name = "test_rename_RM"
        new_name = "test_rename_RN_new"
        rm = self.store.create_registered_model(name)
        self.store.create_model_version(name, "model_id_0", "test", "application_1234", "tensorflow")
        self.store.create_model_version(name, "model_id_1", "test", "application_1235", "tensorflow")
        mv1d = self.store.get_model_version(name, 1)
        mv2d = self.store.get_model_version(name, 2)
        self.assertEqual(rm.name, name)
        self.assertEqual(mv1d.name, name)
        self.assertEqual(mv2d.name, name)

        # test renaming registered model also updates its models
        self.store.rename_registered_model(name, new_name)
        rm = self.store.get_registered_model(new_name)
        mv1d = self.store.get_model_version(new_name, 1)
        mv2d = self.store.get_model_version(new_name, 2)
        self.assertEqual(rm.name, new_name)
        self.assertEqual(mv1d.name, new_name)
        self.assertEqual(mv2d.name, new_name)

        # test accessing the registered model with the original name will fail
        with self.assertRaises(SubmarineException):
            self.store.rename_registered_model(name, name)

        # invalid name will fail
        with self.assertRaises(SubmarineException):
            self.store.rename_registered_model(name, None)
        with self.assertRaises(SubmarineException):
            self.store.rename_registered_model(name, "")

    def test_delete_registered_model(self):
        name1 = "test_delete_RM"
        name2 = "test_delete_RM_2"
        rm_tags = ["rm_tag1", "rm_tag2"]
        rm1 = self.store.create_registered_model(name1, tags=rm_tags)
        rm2 = self.store.create_registered_model(name2, tags=rm_tags)
        mv_tags = ["mv_tag1", "mv_tag2"]
        rm1mv1 = self.store.create_model_version(
            rm1.name, "model_id_0", "test", "application_1234", "tensorflow", tags=mv_tags
        )
        rm2mv1 = self.store.create_model_version(
            rm2.name, "model_id_1", "test", "application_1234", "tensorflow", tags=mv_tags
        )

        # check store
        rm1d = self.store.get_registered_model(rm1.name)
        self.assertEqual(rm1d.name, name1)
        self.assertEqual(rm1d.tags, rm_tags)
        rm1mv1d = self.store.get_model_version(rm1mv1.name, rm1mv1.version)
        self.assertEqual(rm1mv1d.name, name1)
        self.assertEqual(rm1mv1d.tags, mv_tags)

        # delete registered model
        self.store.delete_registered_model(rm1.name)

        # cannot get model
        with self.assertRaises(SubmarineException):
            self.store.get_registered_model(rm1.name)

        # cannot delete it again
        with self.assertRaises(SubmarineException):
            self.store.delete_registered_model(rm1.name)

        # registered model tag are cascade deleted with the registered model
        for tag in rm_tags:
            with self.assertRaises(SubmarineException):
                self.store.delete_registered_model_tag(rm1.name, tag)

        # models are cascade deleted with the registered model
        with self.assertRaises(SubmarineException):
            self.store.get_model_version(rm1mv1.name, rm1mv1.version)

        # model tags are cascade deleted with the registered model
        for tag in rm_tags:
            with self.assertRaises(SubmarineException):
                self.store.delete_model_version_tag(rm1mv1.name, rm1mv1.version, tag)

        # Other registered models and model versions are not affected
        rm2d = self.store.get_registered_model(rm2.name)
        self.assertEqual(rm2d.name, rm2.name)
        self.assertEqual(rm2d.tags, rm2.tags)
        rm2mv1 = self.store.get_model_version(rm2mv1.name, rm2mv1.version)
        self.assertEqual(rm2mv1.name, rm2mv1.name)
        self.assertEqual(rm2mv1.tags, rm2mv1.tags)

    def _compare_registered_model_names(self, results: List[RegisteredModel], rms: List[RegisteredModel]):
        result_names = {result.name for result in results}
        rm_names = {rm.name for rm in rms}

        self.assertEqual(result_names, rm_names)

    def test_list_registered_model(self):
        rms = [self.store.create_registered_model(f"test_list_RM_{i}") for i in range(10)]

        results = self.store.list_registered_model()
        self.assertEqual(len(results), 10)
        self._compare_registered_model_names(results, rms)

    def test_list_registered_model_filter_with_string(self):
        rms = [
            self.store.create_registered_model("A"),
            self.store.create_registered_model("AB"),
            self.store.create_registered_model("B"),
            self.store.create_registered_model("ABA"),
            self.store.create_registered_model("AAA"),
        ]

        results = self.store.list_registered_model(filter_str="A")
        self.assertEqual(len(results), 4)
        self._compare_registered_model_names(rms[:2] + rms[3:], results)

        results = self.store.list_registered_model(filter_str="AB")
        self.assertEqual(len(results), 2)
        self._compare_registered_model_names([rms[1], rms[3]], results)

        results = self.store.list_registered_model(filter_str="ABA")
        self.assertEqual(len(results), 1)
        self._compare_registered_model_names([rms[3]], results)

        results = self.store.list_registered_model(filter_str="ABC")
        self.assertEqual(len(results), 0)
        self.assertEqual(results, [])

    def test_list_registered_model_filter_with_tags(self):
        tags = ["tag1", "tag2", "tag3"]
        rms = [
            self.store.create_registered_model("test1"),
            self.store.create_registered_model("test2", tags=tags[0:1]),
            self.store.create_registered_model("test3", tags=tags[1:2]),
            self.store.create_registered_model("test4", tags=[tags[0], tags[2]]),
            self.store.create_registered_model("test5", tags=tags),
        ]

        results = self.store.list_registered_model(filter_tags=tags[0:1])
        self.assertEqual(len(results), 3)
        self._compare_registered_model_names(results, [rms[1], rms[3], rms[4]])

        results = self.store.list_registered_model(filter_tags=tags[0:2])
        self.assertEqual(len(results), 1)
        self._compare_registered_model_names(results, [rms[-1]])

        # empty result
        other_tag = ["tag4"]
        results = self.store.list_registered_model(filter_tags=other_tag)
        self.assertEqual(len(results), 0)
        self.assertEqual(results, [])

        # empty result
        results = self.store.list_registered_model(filter_tags=tags + other_tag)
        self.assertEqual(len(results), 0)
        self.assertEqual(results, [])

    def test_list_registered_model_filter_both(self):
        tags = ["tag1", "tag2", "tag3"]
        rms = [
            self.store.create_registered_model("A"),
            self.store.create_registered_model("AB", tags=[tags[0]]),
            self.store.create_registered_model("B", tags=[tags[1]]),
            self.store.create_registered_model("ABA", tags=[tags[0], tags[2]]),
            self.store.create_registered_model("AAA", tags=tags),
        ]

        results = self.store.list_registered_model()
        self.assertEqual(len(results), 5)
        self._compare_registered_model_names(results, rms)

        results = self.store.list_registered_model(filter_str="A", filter_tags=[tags[0]])
        self.assertEqual(len(results), 3)
        self._compare_registered_model_names(results, [rms[1], rms[3], rms[4]])

        results = self.store.list_registered_model(filter_str="AB", filter_tags=[tags[0]])
        self.assertEqual(len(results), 2)
        self._compare_registered_model_names(results, [rms[1], rms[3]])

        results = self.store.list_registered_model(filter_str="AAA", filter_tags=tags)
        self.assertEqual(len(results), 1)
        self._compare_registered_model_names(results, [rms[-1]])

    @freeze_time("2021-11-11 11:11:11.111000")
    def test_get_registered_model(self):
        name = "test_get_RM"
        tags = ["tag1", "tag2"]
        fake_datetime = datetime.now()
        rm = self.store.create_registered_model(name, tags=tags)
        self.assertEqual(rm.name, name)

        rmd = self.store.get_registered_model(name)
        self.assertEqual(rmd.name, name)
        self.assertEqual(rmd.creation_time, fake_datetime)
        self.assertEqual(rmd.last_updated_time, fake_datetime)
        self.assertEqual(rmd.description, None)
        self.assertEqual(rmd.tags, tags)

    def test_add_registered_model_tag(self):
        name1 = "test_add_RM_tag"
        name2 = "test_add_RM_tag_2"
        tags = ["tag1", "tag2"]
        rm1 = self.store.create_registered_model(name1, tags=tags)
        rm2 = self.store.create_registered_model(name2, tags=tags)
        new_tag = "new tag"
        self.store.add_registered_model_tag(name1, new_tag)
        rmd = self.store.get_registered_model(name1)
        all_tags = [new_tag] + tags
        self.assertEqual(rmd.tags, all_tags)

        # test add the same tag
        same_tag = "tag1"
        self.store.add_registered_model_tag(name1, same_tag)
        rm1d = self.store.get_registered_model(rm1.name)
        self.assertEqual(rm1d.tags, all_tags)

        # does not affect other models
        rm2d = self.store.get_registered_model(rm2.name)
        self.assertEqual(rm2d.tags, tags)

        # cannot set invalid tag
        with self.assertRaises(SubmarineException):
            self.store.add_registered_model_tag(rm1.name, None)
        with self.assertRaises(SubmarineException):
            self.store.add_registered_model_tag(rm1.name, "")

        # cannot use invalid model name
        with self.assertRaises(SubmarineException):
            self.store.add_registered_model_tag(None, new_tag)

        # cannot set tag on deleted registered model
        self.store.delete_registered_model(rm1.name)
        with self.assertRaises(SubmarineException):
            new_tag = "new tag2"
            self.store.add_registered_model_tag(name1, new_tag)

    def test_delete_registered_model_tag(self):
        name1 = "test_delete_RM_tag"
        name2 = "test_delete_RM_tag_2"
        tags = ["tag1", "tag2"]
        rm1 = self.store.create_registered_model(name1, tags=tags)
        rm2 = self.store.create_registered_model(name2, tags=tags)
        new_tag = "new tag"
        self.store.add_registered_model_tag(rm1.name, new_tag)
        self.store.delete_registered_model_tag(rm1.name, new_tag)
        rm1d = self.store.get_registered_model(rm1.name)
        self.assertEqual(rm1d.tags, tags)

        # delete tag that is already deleted
        with self.assertRaises(SubmarineException):
            self.store.delete_registered_model_tag(rm1.name, new_tag)
        rm1d = self.store.get_registered_model(rm1.name)
        self.assertEqual(rm1d.tags, tags)

        # does not affect other models
        rm2d = self.store.get_registered_model(rm2.name)
        self.assertEqual(rm2d.tags, tags)

        # Cannot delete invalid key
        with self.assertRaises(SubmarineException):
            self.store.delete_registered_model_tag(rm1.name, None)
        with self.assertRaises(SubmarineException):
            self.store.delete_registered_model_tag(rm1.name, "")

        # Cannot use invalid model name
        with self.assertRaises(SubmarineException):
            self.store.delete_registered_model_tag(None, "tag1")

        # Cannot delete tag on deleted (non-existed) registered model
        self.store.delete_registered_model(name1)
        with self.assertRaises(SubmarineException):
            self.store.delete_registered_model_tag(name1, "tag1")

    @freeze_time("2021-11-11 11:11:11.111000")
    def test_create_model_version(self):
        model_name = "test_create_MV"
        self.store.create_registered_model(model_name)
        fake_datetime = datetime.now()
        mv1 = self.store.create_model_version(
            model_name, "model_id_0", "test", "application_1234", "tensorflow"
        )
        self.assertEqual(mv1.name, model_name)
        self.assertEqual(mv1.version, 1)
        self.assertEqual(mv1.creation_time, fake_datetime)

        m1d = self.store.get_model_version(mv1.name, mv1.version)
        self.assertEqual(m1d.name, model_name)
        self.assertEqual(m1d.id, "model_id_0")
        self.assertEqual(m1d.user_id, "test")
        self.assertEqual(m1d.experiment_id, "application_1234")
        self.assertEqual(m1d.model_type, "tensorflow")
        self.assertEqual(m1d.current_stage, STAGE_NONE)
        self.assertEqual(m1d.creation_time, fake_datetime)
        self.assertEqual(m1d.last_updated_time, fake_datetime)
        self.assertEqual(m1d.dataset, None)

        # new model for same registered model autoincrement version
        m2 = self.store.create_model_version(
            model_name, "model_id_1", "test", "application_1234", "tensorflow"
        )
        m2d = self.store.get_model_version(m2.name, m2.version)
        self.assertEqual(m2.version, 2)
        self.assertEqual(m2d.version, 2)

        # create model with tags
        tags = ["tag1", "tag2"]
        m3 = self.store.create_model_version(
            model_name, "model_id_2", "test", "application_1234", "tensorflow", tags=tags
        )
        m3d = self.store.get_model_version(m3.name, m3.version)
        self.assertEqual(m3.version, 3)
        self.assertEqual(m3.tags, tags)
        self.assertEqual(m3d.version, 3)
        self.assertEqual(m3d.tags, tags)

        # create model with description
        description = "A test description."
        m4 = self.store.create_model_version(
            model_name,
            "model_id_3",
            "test",
            "application_1234",
            "tensorflow",
            description=description,
        )
        m4d = self.store.get_model_version(m4.name, m4.version)
        self.assertEqual(m4.version, 4)
        self.assertEqual(m4.description, description)
        self.assertEqual(m4d.version, 4)
        self.assertEqual(m4d.description, description)

    def test_update_model_version_description(self):
        name = "test_update_MV_description"
        self.store.create_registered_model(name)
        mv1 = self.store.create_model_version(name, "model_id_0", "test", "application_1234", "tensorflow")
        m1d = self.store.get_model_version(mv1.name, mv1.version)
        self.assertEqual(m1d.name, name)
        self.assertEqual(m1d.version, 1)
        self.assertEqual(m1d.id, "model_id_0")
        self.assertEqual(m1d.description, None)

        # update description
        fake_datetime = datetime.strptime("2021-11-11 11:11:11.111000", "%Y-%m-%d %H:%M:%S.%f")
        with freeze_time(fake_datetime):
            self.store.update_model_version_description(mv1.name, mv1.version, "New description.")
            m1d = self.store.get_model_version(mv1.name, mv1.version)
            self.assertEqual(m1d.name, name)
            self.assertEqual(m1d.version, 1)
            self.assertEqual(m1d.id, "model_id_0")
            self.assertEqual(m1d.description, "New description.")
            self.assertEqual(m1d.last_updated_time, fake_datetime)

    def test_transition_model_version_stage(self):
        name = "test_transition_MV_stage"
        self.store.create_registered_model(name)
        mv1 = self.store.create_model_version(name, "model_id_0", "test", "application_1234", "tensorflow")
        mv2 = self.store.create_model_version(name, "model_id_1", "test", "application_1234", "tensorflow")

        fake_datetime = datetime.strptime("2021-11-11 11:11:11.111000", "%Y-%m-%d %H:%M:%S.%f")
        with freeze_time(fake_datetime):
            self.store.transition_model_version_stage(mv1.name, mv1.version, STAGE_DEVELOPING)
            m1d = self.store.get_model_version(mv1.name, mv1.version)
            self.assertEqual(m1d.current_stage, STAGE_DEVELOPING)

            # check last updated time
            self.assertEqual(m1d.last_updated_time, fake_datetime)
            rmd = self.store.get_registered_model(name)
            self.assertEqual(rmd.last_updated_time, fake_datetime)

        fake_datetime = datetime.strptime("2021-11-11 11:11:22.222000", "%Y-%m-%d %H:%M:%S.%f")
        with freeze_time(fake_datetime):
            self.store.transition_model_version_stage(mv1.name, mv1.version, STAGE_PRODUCTION)
            m1d = self.store.get_model_version(mv1.name, mv1.version)
            self.assertEqual(m1d.current_stage, STAGE_PRODUCTION)

            # check last updated time
            self.assertEqual(m1d.last_updated_time, fake_datetime)
            rmd = self.store.get_registered_model(name)
            self.assertEqual(rmd.last_updated_time, fake_datetime)

        fake_datetime = datetime.strptime("2021-11-11 11:11:22.333000", "%Y-%m-%d %H:%M:%S.%f")
        with freeze_time(fake_datetime):
            self.store.transition_model_version_stage(mv1.name, mv1.version, STAGE_ARCHIVED)
            m1d = self.store.get_model_version(mv1.name, mv1.version)
            self.assertEqual(m1d.current_stage, STAGE_ARCHIVED)

            # check last updated time
            self.assertEqual(m1d.last_updated_time, fake_datetime)
            rmd = self.store.get_registered_model(name)
            self.assertEqual(rmd.last_updated_time, fake_datetime)

        # uncanonical stage
        for uncanonical_stage_name in ["DEVELOPING", "developing", "DevElopIng"]:
            self.store.transition_model_version_stage(mv1.name, mv1.version, STAGE_NONE)
            self.store.transition_model_version_stage(mv1.name, mv1.version, uncanonical_stage_name)

            m1d = self.store.get_model_version(mv1.name, mv1.version)
            self.assertEqual(m1d.current_stage, STAGE_DEVELOPING)

        # Not matching stages
        with self.assertRaises(SubmarineException):
            self.store.transition_model_version_stage(mv1.name, mv1.version, None)
        # Not matching stages
        with self.assertRaises(SubmarineException):
            self.store.transition_model_version_stage(mv1.name, mv1.version, "stage")

        # No change for other model
        m2d = self.store.get_model_version(mv2.name, mv2.version)
        self.assertEqual(m2d.current_stage, STAGE_NONE)

    def test_delete_model_version(self):
        name = "test_for_delete_MV"
        tags = ["tag1", "tag2"]
        self.store.create_registered_model(name)
        mv = self.store.create_model_version(
            name, "model_id_0", "test", "application_1234", "tensorflow", tags=tags
        )
        mvd = self.store.get_model_version(mv.name, mv.version)
        self.assertEqual(mvd.name, name)

        self.store.delete_model_version(name=mv.name, version=mv.version)

        # model tags are cascade deleted with the model
        with self.assertRaises(SubmarineException):
            self.store.delete_model_version_tag(mv.name, mv.version, tags[0])
        with self.assertRaises(SubmarineException):
            self.store.delete_model_version_tag(mv.name, mv.version, tags[1])

        # cannot get a deleted model
        with self.assertRaises(SubmarineException):
            self.store.get_model_version(mv.name, mv.version)

        # cannot update description of a deleted model
        with self.assertRaises(SubmarineException):
            self.store.update_model_version_description(mv.name, mv.version, "New description.")

        # cannot delete a non-existing version
        with self.assertRaises(SubmarineException):
            self.store.delete_model_version(name=mv.name, version=None)

        # cannot delete a non-existing model name
        with self.assertRaises(SubmarineException):
            self.store.delete_model_version(name=None, version=mv.version)

    @freeze_time("2021-11-11 11:11:11.111000")
    def test_get_model_version(self):
        name = "test_get_MV"
        tags = ["tag1", "tag2"]
        self.store.create_registered_model(name)
        fake_datetime = datetime.now()
        mv = self.store.create_model_version(
            name, "model_id_0", "test", "application_1234", "tensorflow", tags=tags
        )
        self.assertEqual(mv.creation_time, fake_datetime)
        self.assertEqual(mv.last_updated_time, fake_datetime)
        mvd = self.store.get_model_version(mv.name, mv.version)
        self.assertEqual(mvd.name, name)
        self.assertEqual(mvd.id, "model_id_0")
        self.assertEqual(mvd.user_id, "test")
        self.assertEqual(mvd.experiment_id, "application_1234")
        self.assertEqual(mvd.model_type, "tensorflow")
        self.assertEqual(mvd.current_stage, STAGE_NONE)
        self.assertEqual(mvd.creation_time, fake_datetime)
        self.assertEqual(mvd.last_updated_time, fake_datetime)
        self.assertEqual(mvd.dataset, None)
        self.assertEqual(mvd.description, None)
        self.assertEqual(mvd.tags, tags)

    def _compare_model_versions(self, results: List[ModelVersion], mms: List[ModelVersion]) -> None:
        result_versions = {result.version for result in results}
        model_versions = {mm.version for mm in mms}

        self.assertEqual(result_versions, model_versions)

    @freeze_time("2021-11-11 11:11:11.111000")
    def test_list_model_versions(self):
        name1 = "test_list_models_1"
        name2 = "test_list_models_2"
        self.store.create_registered_model(name1)
        self.store.create_registered_model(name2)
        tags = ["tag1", "tag2", "tag3"]
        models = [
            self.store.create_model_version(name1, "model_id_0", "test", "application_1234", "tensorflow"),
            self.store.create_model_version(
                name1, "model_id_1", "test", "application_1234", "tensorflow", tags=[tags[0]]
            ),
            self.store.create_model_version(
                name1, "model_id_2", "test", "application_1234", "tensorflow", tags=[tags[1]]
            ),
            self.store.create_model_version(
                name1,
                "model_id_3",
                "test",
                "application_1234",
                "tensorflow",
                tags=[tags[0], tags[2]],
            ),
            self.store.create_model_version(
                name1, "model_id_4", "test", "application_1234", "tensorflow", tags=tags
            ),
        ]

        results = self.store.list_model_versions(name1)
        self.assertEqual(len(results), 5)
        self._compare_model_versions(results, models)

        results = self.store.list_model_versions(name1, filter_tags=tags[0:1])
        self.assertEqual(len(results), 3)
        self._compare_model_versions(results, [models[1], models[3], models[4]])

        results = self.store.list_model_versions(name1, filter_tags=tags[0:2])
        self.assertEqual(len(results), 1)
        self._compare_model_versions(results, [models[-1]])

        # empty result
        other_tag = ["tag4"]
        results = self.store.list_model_versions(name1, filter_tags=other_tag)
        self.assertEqual(len(results), 0)

        # empty result
        results = self.store.list_model_versions(name1, filter_tags=tags + other_tag)
        self.assertEqual(len(results), 0)

        # empty result for other models
        results = self.store.list_model_versions(name2)
        self.assertEqual(len(results), 0)
        results = self.store.list_model_versions(name2, filter_tags=tags)
        self.assertEqual(len(results), 0)

    def test_get_model_version_uri(self):
        name = "test_get_model_version_uri"
        self.store.create_registered_model(name)
        mv = self.store.create_model_version(name, "model_id_0", "test", "application_1234", "tensorflow")
        uri = self.store.get_model_version_uri(mv.name, mv.version)
        self.assertEqual(uri, f"s3://submarine/registry/{mv.id}/{mv.name}/{mv.version}")

        # cannot retrieve URI for deleted model version
        self.store.delete_model_version(mv.name, mv.version)
        with self.assertRaises(SubmarineException):
            self.store.get_model_version_uri(mv.name, mv.version)

    def test_add_model_version_tag(self):
        name1 = "test_add_MV_tag"
        name2 = "test_add_MV_tag_2"
        tags = ["tag1", "tag2"]
        self.store.create_registered_model(name1)
        self.store.create_registered_model(name2)
        rm1mv1 = self.store.create_model_version(
            name1, "model_id_0", "test", "application_1234", "tensorflow", tags=tags
        )
        rm1mv2 = self.store.create_model_version(
            name1, "model_id_1", "test", "application_1234", "tensorflow", tags=tags
        )
        rm2mv1 = self.store.create_model_version(
            name2, "model_id_2", "test", "application_1234", "tensorflow", tags=tags
        )
        new_tag = "new tag"
        self.store.add_model_version_tag(rm1mv1.name, rm1mv1.version, new_tag)
        all_tags = [new_tag] + tags
        rm1m1d = self.store.get_model_version(rm1mv1.name, rm1mv1.version)
        self.assertEqual(rm1m1d.name, name1)
        self.assertEqual(rm1m1d.tags, all_tags)

        # test add a same tag
        same_tag = "tag1"
        self.store.add_model_version_tag(rm1mv1.name, rm1mv1.version, same_tag)
        mvd = self.store.get_model_version(rm1mv1.name, rm1mv1.version)
        self.assertEqual(mvd.tags, all_tags)

        # does not affect other models
        rm1m2d = self.store.get_model_version(rm1mv2.name, rm1mv2.version)
        self.assertEqual(rm1m2d.name, name1)
        self.assertEqual(rm1m2d.tags, tags)
        rm2mv1 = self.store.get_model_version(rm2mv1.name, rm2mv1.version)
        self.assertEqual(rm2mv1.name, name2)
        self.assertEqual(rm2mv1.tags, tags)

        # cannot add an invalid tag
        with self.assertRaises(SubmarineException):
            self.store.add_model_version_tag(rm1mv1.name, rm1mv1.version, None)
        with self.assertRaises(SubmarineException):
            self.store.add_model_version_tag(rm1mv1.name, rm1mv1.version, "")

        # cannot add tag on deleted (non-existed) model
        self.store.delete_model_version(rm1mv1.name, rm1mv1.version)
        with self.assertRaises(SubmarineException):
            self.store.add_model_version_tag(rm1mv1.name, rm1mv1.version, same_tag)

    def test_delete_model_tag(self):
        name1 = "test_delete_MV_tag"
        name2 = "test_delete_MV_tag_2"
        tags = ["tag1", "tag2"]
        self.store.create_registered_model(name1)
        self.store.create_registered_model(name2)
        rm1mv1 = self.store.create_model_version(
            name1, "model_id_0", "test", "application_1234", "tensorflow", tags=tags
        )
        rm1m2 = self.store.create_model_version(
            name1, "model_id_1", "test", "application_1234", "tensorflow", tags=tags
        )
        rm2mv1 = self.store.create_model_version(
            name2, "model_id_2", "test", "application_1234", "tensorflow", tags=tags
        )
        new_tag = "new tag"
        self.store.add_model_version_tag(rm1mv1.name, rm1mv1.version, new_tag)
        self.store.delete_model_version_tag(rm1mv1.name, rm1mv1.version, new_tag)
        rm1m1d = self.store.get_model_version(rm1mv1.name, rm1mv1.version)
        self.assertEqual(rm1m1d.tags, tags)

        # deleting a tag does not affect other models
        self.store.delete_model_version_tag(rm1mv1.name, rm1mv1.version, tags[0])
        rm1m1d = self.store.get_model_version(rm1mv1.name, rm1mv1.version)
        rm1m2d = self.store.get_model_version(rm1m2.name, rm1m2.version)
        rm2mv1 = self.store.get_model_version(rm2mv1.name, rm2mv1.version)
        self.assertEqual(rm1m1d.tags, tags[1:])
        self.assertEqual(rm1m2d.tags, tags)
        self.assertEqual(rm2mv1.tags, tags)

        # delete a tag that is already deleted
        with self.assertRaises(SubmarineException):
            self.store.delete_model_version_tag(rm1mv1.name, rm1mv1.version, tags[0])
        rm1m1d = self.store.get_model_version(rm1mv1.name, rm1mv1.version)
        self.assertEqual(rm1m1d.tags, tags[1:])

        # cannot delete tag with invalid value
        with self.assertRaises(SubmarineException):
            self.store.delete_model_version_tag(rm1mv1.name, rm1mv1.version, None)
        with self.assertRaises(SubmarineException):
            self.store.delete_model_version_tag(rm1mv1.name, rm1mv1.version, "")

        # cannot delete tag on deleted (non-existed) model
        self.store.delete_model_version(rm1m2.name, rm1m2.version)
        with self.assertRaises(SubmarineException):
            self.store.delete_model_version_tag(rm1m2.name, rm1m2.version, tags[0])

        # cannot use invalid model name or version
        with self.assertRaises(SubmarineException):
            self.store.delete_model_version_tag(None, rm1mv1.version, tags[1])
        with self.assertRaises(SubmarineException):
            self.store.delete_model_version_tag(rm1mv1.name, None, tags[1])
