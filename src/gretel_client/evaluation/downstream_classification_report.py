from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Union

from gretel_client.config import RunnerMode
from gretel_client.evaluation.reports import BaseReport, ReportDictType
from gretel_client.projects.common import DataSourceTypes, RefDataTypes
from gretel_client.projects.models import Model
from gretel_client.projects.projects import Project


class DownstreamClassificationReport(BaseReport):
    """Represents a Downstream Classification Report. This class can be used to create a report.

    Args:
        project: Optional project associated with the report. If no project is passed, a temp project (:obj:`gretel_client.projects.projects.tmp_project`) will be used.
        data_source: Data source used for the report (generally your synthetic data).
        ref_data: Reference data used for the report (generally your real data, i.e. the training data for your gretel model).
        output_dir: Optional directory path to write the report to. If the directory does not exist, the path will be created for you.
        runner_mode: Determines where to run the model. See :obj:`gretel_client.config.RunnerMode` for a list of valid modes. Manual mode is not explicitly supported.
        target: The field which the downstream classifiers are trained to predict.  Must be present in both data_source and ref_data.
        holdout: The ratio of data to hold out from ref_data (i.e., your real data) as a test set.  Must be between 0.0 and 1.0.
        models: The list of classifier models to train.  If absent or an empty list, use all supported models.
        metric: The metric used to sort classifier results.  "Accuracy" by default.
    """

    _model_dict: dict = {
        "schema_version": "1.0",
        "name": "evaluate downstream classification model",
        "models": [
            {
                "evaluate": {
                    "task": {"type": "classification"},
                    "data_source": "__tmp__",
                    "params": {
                        "target": None,
                        "holdout": 0.2,
                        "models": [],
                        "metric": "acc",
                    },
                }
            }
        ],
    }

    @property
    def model_config(self) -> dict:
        return self._model_dict

    # TODO alternative with config file??
    def __init__(
        self,
        *,
        target: str,
        holdout: float = 0.2,
        models: List[str] = [],
        metric: str = "acc",
        project: Optional[Project] = None,
        name: Optional[str] = None,
        data_source: DataSourceTypes,
        ref_data: RefDataTypes,
        output_dir: Optional[Union[str, Path]] = None,
        runner_mode: Optional[RunnerMode] = RunnerMode.CLOUD,
    ):
        if not isinstance(runner_mode, RunnerMode):
            raise ValueError("Invalid runner_mode type, must be RunnerMode enum.")

        if runner_mode == RunnerMode.MANUAL:
            raise ValueError("Cannot use manual mode. Please use CLOUD or LOCAL.")

        if not target:
            raise ValueError("A nonempty target is required.")

        if holdout <= 0 or holdout >= 1.0:
            raise ValueError("Holdout must be between 0.0 and 1.0.")

        # Update the model name if one was provided
        if name is not None:
            self._model_dict["name"] = name

        # Update the report params in our config
        params = self._model_dict["models"][0]["evaluate"]["params"]
        params["target"] = target
        params["holdout"] = holdout
        params["models"] = models
        params["metric"] = metric

        super().__init__(project, data_source, ref_data, output_dir, runner_mode)

    def _run_cloud(self, model: Model):
        super()._run_cloud(model, base_artifact_name="classification_report")

    def _run_local(self, model: Model):
        super()._run_local(model, base_artifact_name="classification_report")

    def peek(self) -> Optional[ReportDictType]:
        super()._check_model_run()
        # Will return dict {"field": "average_metric_difference", "value": \d\d}
        if self._report_dict is not None:
            _summary = self._report_dict.get("summary")
            if _summary:
                return _summary[0]
