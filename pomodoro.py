import click
import json
import os
import sys


HOME_DIRECTORY = os.path.join(os.path.expanduser('~'), '.pomodoro/')
DATA_FILE = os.path.join(HOME_DIRECTORY, 'data.json')


class TaskAlreadyExistsError(Exception):
    pass


class TaskDoesNotExistError(Exception):
    pass


class TaskAlreadyCompleteError(Exception):
    pass


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def save_data_file_content(data):
    with open(DATA_FILE, mode='wb') as f:
        f.write(json.dumps(data, indent=2).encode('utf-8'))


def get_data_file_conent():
    if os.path.isfile(DATA_FILE):
        with open(DATA_FILE, mode='rb') as f:
            non_empty_lines = filter(lambda x: bool(x.trim()), f.readlines())
            if non_empty_lines:
                f.seek(0)
                return json.loads(f.read().decode('utf-8'))
    else:
        if not os.path.isdir(HOME_DIRECTORY):
            os.mkdir(HOME_DIRECTORY)
        initial_data = {
            'tasks': {},
        }
        save_data_file_content(initial_data)
        return initial_data


def add_task(task_id, estimation):
    data = get_data_file_conent()
    tasks = data['tasks']
    if task_id not in tasks.keys():
        tasks[task_id] = {'id': task_id, 'estimation': estimation, 'effort': None, 'completed': False}
        save_data_file_content(data)
    else:
        raise TaskAlreadyExistsError()


def complete_task(task_id, effort=None):
    data = get_data_file_conent()
    tasks = data['tasks']
    if task_id not in tasks.keys():
        raise TaskDoesNotExistError()
    elif tasks.get('completed'):
        raise TaskAlreadyCompleteError()
    else:
        tasks[task_id]['effort'] = effort
        tasks[task_id]['completed'] = True
    save_data_file_content(data)


def get_tasks():
    tasks = get_data_file_conent()['tasks']
    ids_and_tasks = tasks.items()
    if not ids_and_tasks:
        return []
    ids_, tasks = zip(*sorted(ids_and_tasks))
    return tasks


def get_active_tasks():
    return filter(lambda x: not x['completed'], get_tasks())


def get_completed_tasks():
    return filter(lambda x: x['completed'], get_tasks())


def get_task(task_id):
    return get_data_file_conent()['tasks'].get(task_id)


def strong(x):
    return click.style(x, fg='green')


def task_repr(task):
    done_part = ''
    if task['completed']:
        effort = task['effort']
        if effort:
            done_part = ', DONE in {} pomodoros.'.format(effort)
        else:
            done_part = ', DONE (effort not recorded).'
    return '{}, {} Story Points{}'.format(strong(task['id']), task['estimation'], done_part)


@click.group()
def cli():
    pass


# noinspection PyIncorrectDocstring
@cli.command()
@click.argument('task_id', type=str)
@click.argument('estimation', type=int)
def add(task_id, estimation):
    """ Adds a task - Args: task_id, estimation."""
    try:
        add_task(task_id, estimation)
    except TaskAlreadyExistsError:
        eprint('Task {} already exists'.format(strong(task_id)))
        exit(1)


# noinspection PyIncorrectDocstring,PyShadowingBuiltins
@cli.command()
@click.option('--all', '-a', is_flag=True, help='Includes completed tasks')
@click.option('--completed', '-c', is_flag=True, help='Only completed tasks')
def ls(all, completed):
    """ Lists tasks (only active ones by default) """
    if all:
        tasks = get_tasks()
    elif completed:
        tasks = get_completed_tasks()
    else:
        tasks = get_active_tasks()
    list(map(lambda x: print(task_repr(x)), tasks))


# noinspection PyIncorrectDocstring
@cli.command()
@click.argument('task_id', type=str)
@click.argument('effort', required=False, type=str)
@click.option('--no-effort', is_flag=True, default=False,
              help='In order to complete a task without tracking an effort, you must expliscitly pass this flag.')
def complete(task_id, effort, no_effort):
    """ Complete a task - Args: task_id, [effort] """
    try:
        if no_effort:
            complete_task(task_id)
        elif effort:
            complete_task(task_id, effort)
        else:
            # Check if task doesn't exist here in order to have better hints to the user.
            # The `TaskDoesNotExistError` is raised too late by `complete_task`.
            if not get_task(task_id):
                eprint('Task {} does not exist.'.format(strong(task_id)))
                exit(1)
            eprint('You must either pass a second positional argument effort or the --no-effort flag')
            exit(1)
    except TaskDoesNotExistError:
        # Shouldn't happen, but keeping this for now.
        eprint('Task {} does not exist.'.format(strong(task_id)))
        exit(1)
    except TaskAlreadyCompleteError:
        eprint('Task {} is already complete. If you need to change some of it\'s values, edit the {} file '
               'manually.'.format(strong(task_id), strong(DATA_FILE)))
        exit(1)
