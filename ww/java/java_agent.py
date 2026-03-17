from jpype import startJVM, JVMNotFoundException, isJVMStarted, JClass


class JavaAgentConnector:
    def __init__(self, jar_path="/path/to/java-agent.jar", agent_class="com.example.Agent"):
        self.jar_path = jar_path
        self.agent_class = agent_class
        self.agent_instance = None

    def connect(self):
        try:
            if not isJVMStarted():
                startJVM(f"-Djava.class.path={self.jar_path}", "-ea")
            AgentClass = JClass(self.agent_class)
            self.agent_instance = AgentClass()
            print(f"Connected to Java agent: {self.agent_class}")
            return True
        except JVMNotFoundException:
            print("JVM not found. Ensure Java is installed.")
            return False
        except Exception as e:
            print(f"Failed to connect: {e}")
            return False

    def get_jvm_info(self):
        if not self.agent_instance:
            print("Not connected to agent")
            return None
        try:
            return self.agent_instance.getJVMInfo()
        except Exception as e:
            print(f"Error getting JVM info: {e}")
            return None

    def get_memory_usage(self):
        if not self.agent_instance:
            print("Not connected to agent")
            return None
        try:
            return self.agent_instance.getMemoryUsage()
        except Exception as e:
            print(f"Error getting memory usage: {e}")
            return None

    def get_thread_info(self):
        if not self.agent_instance:
            print("Not connected to agent")
            return None
        try:
            return self.agent_instance.getThreadInfo()
        except Exception as e:
            print(f"Error getting thread info: {e}")
            return None

    def disconnect(self):
        self.agent_instance = None
        print("Disconnected from Java agent")
