import codecs
import os

import yaml

from ansiblelater.command.review import Error, Result
from ansiblelater.utils.rulehelper import (get_action_tasks,
                                           get_normalized_task,
                                           get_normalized_yaml, run_yamllint)


def check_yaml_has_content(candidate, settings):
    lines, errors = get_normalized_yaml(candidate, settings)
    description = "the file appears to have no useful content"

    if not lines and not errors:
        errors.append(Error(None, description))

    return Result(candidate.path, errors)


def check_native_yaml(candidate, settings):
    tasks, errors = get_action_tasks(candidate, settings)
    description = "task arguments appear to be in key value rather than YAML format"

    if not errors:
        for task in tasks:
            normal_form, error = get_normalized_task(task, candidate, settings)
            if error:
                errors.extend(error)
                break

            action = normal_form["action"]["__ansible_module__"]
            arguments = normal_form["action"]["__ansible_arguments__"]
            # Cope with `set_fact` where task["set_fact"] is None
            if not task.get(action):
                continue
            if isinstance(task[action], dict):
                continue
            # strip additional newlines off task[action]
            if task[action].strip().split() != arguments:
                errors.append(Error(task["__line__"], description))
    return Result(candidate.path, errors)


def check_yaml_empty_lines(candidate, settings):
    options = "rules: {empty-lines: {max: 1, max-start: 0, max-end: 1}}"
    errors = run_yamllint(candidate, settings, options)
    return Result(candidate.path, errors)


def check_yaml_indent(candidate, settings):
    options = "rules: {indentation: {spaces: 2, check-multi-line-strings: false, indent-sequences: true}}"
    errors = run_yamllint(candidate, settings, options)
    return Result(candidate.path, errors)


def check_yaml_hyphens(candidate, settings):
    options = "rules: {hyphens: {max-spaces-after: 1}}"
    errors = run_yamllint(candidate, settings, options)
    return Result(candidate.path, errors)


def check_yaml_document_start(candidate, settings):
    options = "rules: {document-start: {present: true}}"
    errors = run_yamllint(candidate, settings, options)
    return Result(candidate.path, errors)


def check_yaml_colons(candidate, settings):
    options = "rules: {colons: {max-spaces-before: 0, max-spaces-after: 1}}"
    errors = run_yamllint(candidate, settings, options)
    return Result(candidate.path, errors)


def check_yaml_file(candidate, settings):
    errors = []
    filename = candidate.path

    if os.path.isfile(filename) and os.path.splitext(filename)[1][1:] != "yml":
        errors.append(
            Error(None, "file does not have a .yml extension"))
    elif os.path.isfile(filename) and os.path.splitext(filename)[1][1:] == "yml":
        with codecs.open(filename, mode="rb", encoding="utf-8") as f:
            try:
                yaml.safe_load(f)
            except Exception as e:
                errors.append(
                    Error(e.problem_mark.line + 1, "syntax error: %s" % (e.problem)))

    return Result(candidate.path, errors)
