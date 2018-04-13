import boto3
import botocore
import click


def get_session(profile: str) -> boto3.Session:
    """Returns a boto3 session"""
    if profile:
        return boto3.Session(profile_name=profile)
    else:
        return boto3.Session()


def get_ec2_client(profile: str):
    """Returns the ec2 client"""
    return get_session(profile).resource('ec2')


def get_ec2_instances(project: str, ec2):
    """Return ec2 instances for project"""
    if project:
        filters = [{'Name': 'tag:PROJECT', 'Values': [project]}]
        return ec2.instances.filter(Filters=filters)
    else:
        return ec2.instances.all()


def has_pending_snapshot(volume) -> bool:
    """Returns if the volume has pending snapshots"""
    xs = list(volume.snapshots.all())
    return bool(xs and xs[0].state == 'pending')


@click.group()
def cli():
    """Shotty manages ec2"""


@cli.group('volumes')
def volumes():
    """Commands for volumes"""


@cli.group('snapshots')
def snapshots():
    """Commands for snapshots"""


@volumes.command('list')
@click.option('--profile', default=None, help='The profile to be used')
@click.option('--project', default=None, help='The project to be used')
def list_volumes(profile: str, project: str):
    """List ec2 volumes"""
    xs = get_ec2_instances(project, get_ec2_client(profile))

    for i in xs:
        for v in i.volumes.all():
            print(", ".join((
                v.id,
                i.id,
                v.state,
                str(v.size) + "GiB",
                v.encrypted and "Encrypted" or "Not Encrypted"
            )))
    return


@cli.group('instances')
def instances():
    """Commands for instances"""


@instances.command('list')
@click.option('--profile', default=None, help='The profile to be used')
@click.option('--project', default=None, help='The project to be used')
def list_instances(profile: str, project: str):
    """List ec2 instances"""
    xs = get_ec2_instances(project, get_ec2_client(profile))

    for i in xs:
        tags: dict = {k['Key']: k['Value'] for k in i.tags or []}
        info = ', '.join((
            i.id,
            i.instance_type,
            i.placement['AvailabilityZone'],
            i.state['Name'],
            i.public_dns_name,
            tags.get('PROJECT', '<no project>')
        ))
        print(info)
    return


@instances.command('stop')
@click.option('--profile', default=None, help='The profile to be used')
@click.option('--project', default=None, help='Only instances for project')
def stop_instances(profile: str, project: str):
    """Stop ec2 instances"""
    xs = get_ec2_instances(project, get_ec2_client(profile))
    for i in xs:
        print(f"Stopping {i.id}...")
        try:
            i.stop()
        except botocore.exceptions.ClientError as e:
            print(f"Could not stop {i.id} -> {e}")
    return


@instances.command('wait_until_stopped')
@click.option('--profile', default=None, help='The profile to be used')
@click.option('--project', default=None, help='Only instances for project')
def wait_until_stopped_instances(profile: str, project: str):
    """wait until instances are stopped"""
    xs = get_ec2_instances(project, get_ec2_client(profile))
    for i in xs:
        print(f"Waiting on {i.id}...")
        i.wait_until_stopped()
    return


@instances.command('start')
@click.option('--profile', default=None, help='The profile to be used')
@click.option('--project', default=None, help='Only instances for project')
def start_instances(profile: str, project: str):
    """Start ec2 instances"""
    xs = get_ec2_instances(project, get_ec2_client(profile))
    for i in xs:
        print(f"Starting {i.id}...")
        try:
            i.start()
        except botocore.exceptions.ClientError as e:
            print(f"Could not start {i.id} -> {e}")
    return


@instances.command('wait_until_running')
@click.option('--profile', default=None, help='The profile to be used')
@click.option('--project', default=None, help='Only instances for project')
def wait_until_running(profile: str, project: str):
    """Wait until ec2 instances are running"""
    xs = get_ec2_instances(project, get_ec2_client(profile))
    for i in xs:
        print(f"Waiting on {i.id}...")
        i.wait_until_running()
    return


@instances.command('snapshots')
@click.option('--profile', default=None, help='The profile to be used')
@click.option('--project', default=None, help='Only instances for project')
def create_snapshots(profile: str, project: str):
    """Create snapshots of all volumes"""
    xs = get_ec2_instances(project, get_ec2_client(profile))
    for x in xs:
        print(f"Stopping {x.id}")

        x.stop()
        x.wait_until_stopped()

        for v in x.volumes.all():
            if has_pending_snapshot(v):
                print(f"Skipping {v.id}, snapshot already in progress")
                continue

            print(f"Creating snapshot of {v.id}")
            v.create_snapshot(Description="Created by snappy")

        print(f"Starting {x.id}")

        x.start()
        x.wait_until_running()

    print("Job's done!")
    return


@snapshots.command('list')
@click.option('--profile', default=None, help='The profile to be used')
@click.option('--project', default=None, help='Only instances for project')
@click.option('--all', 'list_all', default=False, is_flag=True,
              help="list all the snapshots, not just the most recent one")
def list_snapshots(profile: str, project: str, list_all: bool):
    """List ec2 snapshots"""
    xs = get_ec2_instances(project, get_ec2_client(profile))
    for i in xs:
        for v in i.volumes.all():
            for s in v.snapshots.all():
                print(", ".join((
                    s.id,
                    v.id,
                    i.id,
                    s.state,
                    s.progress,
                    s.start_time.strftime("%c")
                )))

                if s.state == 'completed' and not list_all:
                    break
    return


if __name__ == "__main__":
    cli()
