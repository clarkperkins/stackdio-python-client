from cmd2 import Cmd


class FormulaMixin(Cmd):
    FORMULA_COMMANDS = ["list", "import", "delete"]

    def do_formulas(self, arg):
        """Entry point to controlling formulas."""

        USAGE = "Usage: formulas COMMAND\nWhere COMMAND is one of: %s" % (
            ", ".join(self.FORMULA_COMMANDS))

        args = arg.split()
        if not args or args[0] not in self.FORMULA_COMMANDS:
            print(USAGE)
            return

        formula_cmd = args[0]
        if formula_cmd == "list":
            self._list_formulas()
        elif formula_cmd == "import":
            self._import_formula(args[1:])
        elif formula_cmd == "delete":
            self._delete_formula(args[1:])

        else:
            print(USAGE)

    def complete_formulas(self, text, line, begidx, endidx):
        # not using line, begidx, or endidx, thus the following pylint disable
        # pylint: disable=W0613
        return [i for i in self.FORMULA_COMMANDS if i.startswith(text)]

    def help_formulas(self):
        print("Manage formulas.")
        print("Sub-commands can be one of:\n\t{0}".format(
            ", ".join(self.FORMULA_COMMANDS)))
        print("Try 'formulas COMMAND' to get help on (most) sub-commands")

    def _list_formulas(self):
        """List all formulas"""

        print("Getting formulas ... ")
        formulas = self.stacks.list_formulas()
        self._print_summary("Formula", formulas)

    def _import_formula(self, args):
        """Import a formula"""

        if len(args) != 1:
            print("Usage: formulas import URL")
            return

        formula_url = args[0]
        print("Importing formula from {0}".format(formula_url))
        formula = self.stacks.import_formula(formula_url, public=False)

        if isinstance(formula, list):
            print("Formula imported, try the 'list' command to monitor status")
        elif formula.get("detail"):
            print("Error importing: {0}".format(formula.get("detail")))

    def _delete_formula(self, args):
        """Delete a formula"""

        args = " ".join(args)
        if len(args) == 0:
            print("Usage: formulas delete TITLE")
            return

        formula_id = self.stacks.get_formula_id(args)

        really = raw_input("Really delete formula {0} (y/n)? ".format(args))
        if really not in ["y", "Y"]:
            print("Aborting deletion")
            return

        self.stacks.delete_formula(formula_id)

        print("Formula deleted, try the 'list' command to monitor status")

