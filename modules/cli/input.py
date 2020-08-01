import argparse


class CustomHelpFormatter(argparse.HelpFormatter):
    def __init__(self, prog):
        super().__init__(prog, max_help_position=40, width=99)

    def _format_action_invocation(self, action):
        if not action.option_strings or action.nargs == 0:
            return super()._format_action_invocation(action)
        default = self._get_default_metavar_for_optional(action)
        args_string = self._format_args(action, default)
        return ", ".join(action.option_strings) + " " + args_string


fmt = lambda prog: CustomHelpFormatter(prog)
parser = argparse.ArgumentParser(
    description="Tool for RTSP that brute-forces routes and credentials, makes screenshots!",
    formatter_class=fmt,
)
parser.add_argument(
    "-t",
    "--targets",
    default="hosts.txt",
    help="the targets on which to scan for open RTSP streams",
)
parser.add_argument(
    "-p",
    "--ports",
    nargs="+",
    default=[554],
    type=int,
    help="the ports on which to search for RTSP streams",
)
parser.add_argument(
    "-r",
    "--routes",
    default="routes.txt",
    help="the path on which to load a custom routes",
)
parser.add_argument(
    "-c",
    "--credentials",
    default="credentials.txt",
    help="the path on which to load a custom credentials",
)
parser.add_argument(
    "-ct",
    "--check-threads",
    default=500,
    type=int,
    help="the number of threads to brute-force the routes",
    metavar="N",
)
parser.add_argument(
    "-bt",
    "--brute-threads",
    default=200,
    type=int,
    help="the number of threads to brute-force the credentials",
    metavar="N",
)
parser.add_argument(
    "-st",
    "--screenshot-threads",
    default=20,
    type=int,
    help="the number of threads to screenshot the streams",
    metavar="N",
)
parser.add_argument(
    "-T", "--timeout", default=2, type=int, help="the timeout to use for sockets"
)
parser.add_argument("-d", "--debug", action="store_true", help="enable the debug logs")
