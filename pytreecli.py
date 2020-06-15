from typing import *
from abc import ABC
import argparse
import cProfile
import datetime


class InvalidUsage(Exception):
    pass


class SubCommand(ABC):
    def __init__(self, name: str, help: str):
        self.name = name
        self.help = help

    def configure_args(self, parser: argparse.ArgumentParser):
        pass

    def run(self, args):
        raise NotImplementedError

    def validate_args(self, args):
        return True


class ParentCommand(SubCommand):
    i = 0

    def __init__(self, name: str, help: str, sub_commands: List[SubCommand]):
        super().__init__(name, help)
        self.sub_commands = sub_commands

        # Generate the member inside "args" that stores the sub-command.
        # This is auto-generated because there's no usage outside of this class..
        self.cmd_arg_name = 'command_'+str(ParentCommand.i)
        ParentCommand.i += 1

    def configure_args(self, parser):
        subparsers = parser.add_subparsers(dest=self.cmd_arg_name)
        ParentCommand.i += 1

        for command in self.sub_commands:
            command_parser = subparsers.add_parser(
                name=command.name,
                help=command.help
            )

            command.configure_args(command_parser)

    def run(self, args):
        requested_command = args.__dict__[self.cmd_arg_name]

        if requested_command is None:
            raise InvalidUsage()

        for command in self.sub_commands:
            if command.name == args.__dict__[self.cmd_arg_name]:
                command.validate_args(args)
                command.run(args)
                break


def run(title: str,
        description: str,
        commands: List[SubCommand]
        ):

    parser = argparse.ArgumentParser(
        prog=title,
        description=description
    )

    parser.add_argument('--profile', action='store_true',
                        help="Run the command with profiling and print stats")

    parser.add_argument('--count-time', action='store_true',
                        help="Print the amount of time it took to execute the command")

    main_command = ParentCommand('main', description, commands)
    main_command.configure_args(parser)
    args = parser.parse_args()
    pr = None

    if args.profile:
        pr = cProfile.Profile()
        pr.enable()

    if args.count_time:
        start_time = datetime.datetime.now()
    else:
        start_time = None

    try:
        main_command.run(args)
    except InvalidUsage as e:
        print(str(e))
        print()
        parser.print_help()

    if args.profile:
        pr.disable()
        pr.print_stats(sort='time')

    if args.count_time:
        elapsed_time = datetime.datetime.now() - start_time
        print(str(elapsed_time))
