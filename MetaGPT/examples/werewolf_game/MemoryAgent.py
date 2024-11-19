from metagpt.actions import Action
from metagpt.roles import Role
from metagpt.team import Team
from metagpt.environment import Message
from metagpt.logs import logger

# Step 1: Define Actions for Each Role
class FetchMemory(Action):
    """Fetch data from the agent's memory using its API."""
    PROMPT_TEMPLATE: str = "Fetch memory data for {memory_type}."

    async def run(self, memory_type: str):
        # Simulate API call to fetch memory
        return f"Data for memory type: {memory_type}"


class AnalyzeData(Action):
    """Analyze memory data."""
    PROMPT_TEMPLATE: str = "Analyze the provided memory data: {data}"

    async def run(self, data: str):
        return f"Analysis result for: {data}"


class WriteReport(Action):
    """Generate a report based on analysis."""
    PROMPT_TEMPLATE: str = "Generate a report based on analysis: {analysis}"

    async def run(self, analysis: str):
        return f"Report generated from analysis: {analysis}"


class QualityCheck(Action):
    """Perform quality check on the report."""
    PROMPT_TEMPLATE: str = "Perform quality checks on the following report: {report}"

    async def run(self, report: str):
        return f"Quality checked: {report}"


# Step 2: Define Roles
class MemoryAgent(Role):
    """Agent responsible for memory retrieval."""
    name = "MemoryAgent"

    def __init__(self, memory_type: str, **kwargs):
        super().__init__(**kwargs)
        self.memory_type = memory_type
        self.set_actions([FetchMemory])

    async def _act(self) -> Message:
        data = await self.get_action("FetchMemory").run(self.memory_type)
        return Message(content=data, role=self.name)


class AnalystAgent(Role):
    """Agent responsible for data analysis."""
    name = "AnalystAgent"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([AnalyzeData])
        self._watch(["MemoryAgent"])

    async def _act(self) -> Message:
        memory_data = self.get_memories()[0].content
        analysis = await self.get_action("AnalyzeData").run(memory_data)
        return Message(content=analysis, role=self.name)


class ReporterAgent(Role):
    """Agent responsible for generating reports."""
    name = "ReporterAgent"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([WriteReport])
        self._watch(["AnalystAgent"])

    async def _act(self) -> Message:
        analysis = self.get_memories()[0].content
        report = await self.get_action("WriteReport").run(analysis)
        return Message(content=report, role=self.name)


class QAAgent(Role):
    """Agent responsible for quality assurance."""
    name = "QAAgent"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([QualityCheck])
        self._watch(["ReporterAgent"])

    async def _act(self) -> Message:
        report = self.get_memories()[0].content
        quality_result = await self.get_action("QualityCheck").run(report)
        return Message(content=quality_result, role=self.name)


# Step 3: Initialize and Run the Team
def main():
    team = Team()

    # Hire 10 agents with unique memories and responsibilities
    memory_types = [f"MemoryType{i}" for i in range(1, 11)]
    for i, memory_type in enumerate(memory_types, start=1):
        team.hire([
            MemoryAgent(memory_type=memory_type, name=f"MemoryAgent{i}"),
            AnalystAgent(name=f"AnalystAgent{i}"),
            ReporterAgent(name=f"ReporterAgent{i}"),
            QAAgent(name=f"QAAgent{i}")
        ])

    # Define project idea
    idea = "Collaboratively generate and review memory-based reports."
    logger.info(f"Starting project: {idea}")

    # Run the project simulation
    team.run_project(idea)
    team.run(n_round=10)


if __name__ == "__main__":
    main()
