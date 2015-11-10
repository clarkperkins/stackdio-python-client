import json

from cmd2 import Cmd

from stackdio.client.exceptions import StackException


class StackMixin(Cmd):

    STACK_ACTIONS = ["start", "stop", "launch_existing", "terminate", "provision", "custom"]
    STACK_COMMANDS = ["list", "launch_from_blueprint", "history", "hostnames", 
        "delete", "logs", "access_rules"] + STACK_ACTIONS

    VALID_LOGS = {
        "provisioning": "provisioning.log",
        "provisioning-error": "provisioning.err",
        "global-orchestration": "global_orchestration.log",
        "global-orchestration-error": "global_orchestration.err",
        "orchestration": "orchestration.log",
        "orchestration-error": "orchestration.err",
        "launch": "launch.log",
    }

    def do_stacks(self, arg):
        """Entry point to controlling."""
       
        USAGE = "Usage: stacks COMMAND\nWhere COMMAND is one of: %s" % (
            ", ".join(self.STACK_COMMANDS))

        # We don't want multiline commands, so include anything after a terminator as well
        args = arg.parsed.raw.split()[1:]
        if not args or args[0] not in self.STACK_COMMANDS:
            print(USAGE)
            return

        stack_cmd = args[0]

        if stack_cmd == "list":
            self._list_stacks()
        elif stack_cmd == "launch_from_blueprint":
            self._launch_stack(args[1:])
        elif stack_cmd == "history":
            self._stack_history(args[1:])
        elif stack_cmd == "hostnames":
            self._stack_hostnames(args[1:])
        elif stack_cmd == "delete":
            self._stack_delete(args[1:])
        elif stack_cmd == "logs":
            self._stack_logs(args[1:])
        elif stack_cmd == "access_rules":
            self._stack_access_rules(args[1:])
        elif stack_cmd in self.STACK_ACTIONS:
            self._stack_action(args)

        else:
            print(USAGE)
   
    def complete_stacks(self, text, line, begidx, endidx):
        # not using line, begidx, or endidx, thus the following pylint disable
        # pylint: disable=W0613
        return [i for i in self.STACK_COMMANDS if i.startswith(text)]

    def help_stacks(self):
        print("Manage stacks.")
        print("Sub-commands can be one of:\n\t{0}".format(
            ", ".join(self.STACK_COMMANDS)))
        print("Try 'stacks COMMAND' to get help on (most) sub-commands")

    def _list_stacks(self):
        """List all running stacks"""

        print("Getting running stacks ... ")
        stacks = self.stacks.list_stacks()
        self._print_summary("Stack", stacks)

    def _launch_stack(self, args):
        """Launch a stack from a blueprint.  
        Must provide blueprint name and stack name"""
        
        if len(args) != 2:
            print("Usage: stacks launch BLUEPRINT_NAME STACK_NAME")
            return

        blueprint_name = args[0]
        stack_name = args[1]

        try:
            blueprint_id = self.stacks.get_blueprint_id(blueprint_name)
        except StackException:
            print(self.colorize(
                "Blueprint [{0}] does not exist".format(blueprint_name),
                "red"))
            return

        print("Launching stack [{0}] from blueprint [{1}]".format(
            stack_name, blueprint_name))
        
        stack_data = {
            "blueprint": blueprint_id,
            "title": stack_name,
            "description": "Launched from blueprint %s" % (blueprint_name),
            "namespace": stack_name,
            "max_retries": 1,
        }
        results = self.stacks.create_stack(stack_data)
        print("Stack launch results:\n{0}".format(results))

    def _get_stack_id(self, stack_name):
        """Validate that a stack exists"""

        try:
            return self.stacks.get_stack_id(stack_name)
        except StackException:
            print(self.colorize(
                "Stack [{0}] does not exist".format(stack_name),
                "red"))
            raise

    def _stack_action(self, args):
        """Perform an action on a stack."""

        if len(args) == 1:
            print("Usage: stacks {0} STACK_NAME".format(args[0]))
            return
        elif args[0] != "custom" and len(args) != 2:
            print("Usage: stacks ACTION STACK_NAME")
            print("Where ACTION is one of {0}".format(
                ", ".join(self.STACK_ACTIONS)))
            return
        elif args[0] == "custom" and len(args) < 4:
            print("Usage: stacks custom STACK_NAME HOST_TARGET COMMAND")
            print("Where command can be arbitrarily long with spaces")
            return
       
        if args[0] not in self.STACK_ACTIONS:
            print(self.colorize(
                "Invalid action - must be one of {0}".format(self.STACK_ACTIONS),
                "red"))
            return

        action = "launch" if args[0] == "launch_existing" else args[0]
        stack_name = args[1]

        if action == "terminate":
            really = raw_input("Really terminate stack {0} (y/n)? ".format(args[0]))
            if really not in ["y", "Y"]:
                print("Aborting termination")
                return

        if action == "custom":
            host_target = args[2]
            command = ''
            for token in args[3:]:
                command += token + ' '

        stack_id = self._get_stack_id(stack_name)
        print("Performing [{0}] on [{1}]".format(
            action, stack_name))

        if action == "custom":
            results = self.stacks.do_stack_action(stack_id, "custom", host_target, command)
        else:
            results = self.stacks.do_stack_action(stack_id, action)
        print("Stack action results:\n{0}".format(json.dumps(results, indent=3)))

    def _stack_history(self, args):
        """Print recent history for a stack"""
        # pylint: disable=W0142

        NUM_EVENTS = 20
        if len(args) < 1:
            print("Usage: stacks history STACK_NAME")
            return

        stack_id = self._get_stack_id(args[0])
        history = self.stacks.get_stack_history(stack_id).get("results")
        for event in history[0:min(NUM_EVENTS, len(history))]:
            print("[{created}] {level} // {event} // {status}".format(**event))

    def _stack_hostnames(self, args):
        """Print hostnames for a stack"""

        if len(args) < 1:
            print("Usage: stacks hostnames STACK_NAME")
            return
        
        stack_id = self._get_stack_id(args[0])
        try:
            fqdns = self.stacks.describe_hosts(stack_id)
        except StackException:
            print(self.colorize(
                "Hostnames not available - stack still launching?", "red"))
            raise

        print("Hostnames:")
        for host in fqdns:
            print("  - {0}".format(host))

    def _stack_delete(self, args):
        """Delete a stack.  PERMANENT AND DESTRUCTIVE!!!"""

        if len(args) < 1:
            print("Usage: stacks delete STACK_NAME")
            return

        stack_id = self._get_stack_id(args[0])
        really = raw_input("Really delete stack {0} (y/n)? ".format(args[0]))
        if really not in ["y", "Y"]:
            print("Aborting deletion")
            return
            
        results = self.stacks.delete_stack(stack_id)
        print("Delete stack results: {0}".format(results))
        print(self.colorize(
            "Run 'stacks history {0}' to monitor status of the deletion".format(
            args[0]),
            "green"))

    def _stack_logs(self, args):
        """Get logs for a stack"""
        
        MAX_LINES = 25

        if len(args) < 2:
            print("Usage: stacks logs STACK_NAME LOG_TYPE [LOG_LENGTH]")
            print("LOG_TYPE is one of {0}".format(
                ", ".join(self.stacks.VALID_LOGS.keys())))
            print("This defaults to the last {0} lines of the log.".
                format(MAX_LINES))
            return

        if len(args) >= 3:
            max_lines = args[2] 
        else:
            max_lines = MAX_LINES

        stack_id = self.stacks.get_stack_id(args[0])

        split_arg = self.VALID_LOGS[args[1]].split('.')

        log_text = self.stacks.get_logs(stack_id, log_type=split_arg[0], level=split_arg[1],
                                        tail=max_lines)
        print(log_text)

    def _stack_access_rules(self, args):
        """Get access rules for a stack"""


        COMMANDS = ["list", "add", "delete"]

        if len(args) < 2 or args[0] not in COMMANDS:
            print("Usage: stacks access_rules COMMAND STACK_NAME")
            print("Where COMMAND is one of: %s" % (", ".join(COMMANDS)))
            return
                  
        if args[0] == "list":
            stack_id = self.stacks.get_stack_id(args[1])
            groups = self.stacks.list_access_rules(stack_id)
            print "##", len(groups), "Access Groups"
            for group in groups:
                print "- Name:", group['blueprint_host_definition']['title']
                print "  Description:", group['blueprint_host_definition']['description']
                print "  Rules:"
                for rule in group['rules']:
                    print "   ",rule['protocol'],
                    if rule['from_port'] == rule['to_port']:
                        print "port", rule['from_port'], "allows",
                    else:
                        print "ports", rule['from_port']+"-"+rule['to_port'], "allow",
                    print rule['rule']
                print
            return

        elif args[0] == "add":
            if len(args) < 3:
                print("Usage: stacks access_rules add STACK_NAME GROUP_NAME")
                return
            
            stack_id = self.stacks.get_stack_id(args[1])
            group_id = self.stacks.get_access_rule_id(stack_id, args[2])

            protocol = raw_input("Protocol (tcp, udp, or icmp): ")
            from_port = raw_input("From port: ")
            to_port = raw_input("To port: ")
            rule = raw_input("Rule (IP address or group name): ")

            data = {
                "action": "authorize",
                "protocol": protocol,
                "from_port": from_port,
                "to_port": to_port,
                "rule": rule
            }

            self.stacks.edit_access_rule(group_id, data)

        elif args[0] == "delete":
            if len(args) < 3:
                print("Usage: stacks access_rules delete STACK_NAME GROUP_NAME")
                return

            stack_id = self.stacks.get_stack_id(args[1])
            group_id = self.stacks.get_access_rule_id(stack_id, args[2])

            index = 0

            rules = self.stacks.list_rules_for_group(group_id)

            print
            for rule in rules:
                print str(index)+") ", rule['protocol'],
                if rule['from_port'] == rule['to_port']:
                    print "port", rule['from_port'], "allows",
                else:
                    print "ports", rule['from_port']+"-"+rule['to_port'], "allow",
                print rule['rule']
                index += 1
            print
            delete_index = int(raw_input("Enter the index of the rule to delete: "))

            data = rules[delete_index]
            data['from_port'] = int(data['from_port'])
            data['to_port'] = int(data['to_port'])
            data['action'] = "revoke"

            self.stacks.edit_access_rule(group_id, data)

        print
    
        args[0] = "list"
    
        self._stack_access_rules(args)


