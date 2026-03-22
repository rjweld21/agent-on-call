import json


class TestMessages:
    def test_task_request_to_json(self):
        from agent_on_call.messages import TaskRequest

        req = TaskRequest(
            task_id="task-001",
            description="Research the best database for real-time analytics",
            agent_name="Research - DB Selection",
        )
        data = req.to_json()
        parsed = json.loads(data)
        assert parsed["task_id"] == "task-001"
        assert parsed["type"] == "task_request"

    def test_status_update_from_json(self):
        from agent_on_call.messages import StatusUpdate

        data = json.dumps(
            {
                "type": "status_update",
                "task_id": "task-001",
                "status": "working",
                "detail": "Evaluating PostgreSQL vs ClickHouse",
            }
        )
        update = StatusUpdate.from_json(data)
        assert update.task_id == "task-001"
        assert update.status == "working"

    def test_guidance_request_from_json(self):
        from agent_on_call.messages import GuidanceRequest

        data = json.dumps(
            {
                "type": "guidance_request",
                "task_id": "task-001",
                "question": "Should I prioritize read performance or write throughput?",
                "context": "Both PostgreSQL and ClickHouse are viable options.",
            }
        )
        req = GuidanceRequest.from_json(data)
        assert req.question == "Should I prioritize read performance or write throughput?"

    def test_guidance_response_to_json(self):
        from agent_on_call.messages import GuidanceResponse

        resp = GuidanceResponse(
            task_id="task-001",
            answer="Prioritize read performance for our analytics dashboard use case.",
        )
        data = resp.to_json()
        parsed = json.loads(data)
        assert parsed["type"] == "guidance_response"
        assert "read performance" in parsed["answer"]

    def test_task_result_from_json(self):
        from agent_on_call.messages import TaskResult

        data = json.dumps(
            {
                "type": "task_result",
                "task_id": "task-001",
                "result": "Recommend ClickHouse for read-heavy analytics workloads.",
                "status": "done",
            }
        )
        result = TaskResult.from_json(data)
        assert result.status == "done"
        assert "ClickHouse" in result.result
