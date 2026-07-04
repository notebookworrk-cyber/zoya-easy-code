"""Comprehensive tests for the Zoya AI Platform modules.

Tests cover: llm.py, tools.py, memory.py, embeddings.py, agent.py, rag.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json
import os
import tempfile
import unittest

from zoya.ai.agent import (
    Agent,
    AgentError,
    PlanningAgent,
    create_agent,
)
from zoya.ai.agent import (
    Tool as AgentTool,
)
from zoya.ai.agent import (
    ToolRegistry as AgentToolRegistry,
)
from zoya.ai.embeddings import (
    EmbeddingError,
    TextEmbedding,
    TFIDFVectorizer,
    cosine_similarity,
    simple_tokenize,
)
from zoya.ai.llm import LLMError, MockProvider, create_provider
from zoya.ai.memory import (
    ConversationMemory,
    MemoryError,
    SemanticMemory,
)
from zoya.ai.rag import (
    Document,
    DocumentChunker,
    RAGError,
    RAGIndex,
    RAGRetriever,
)
from zoya.ai.tools import (
    Calculator,
    FileReadTool,
    FileWriteTool,
    PythonExecuteTool,
    ShellTool,
    ToolError,
    WebSearchTool,
    tool,
)
from zoya.ai.tools import Tool as ToolBase
from zoya.ai.tools import ToolRegistry as ToolRegistryBase

# ============================================================================
# LLM Tests
# ============================================================================


class TestLLM(unittest.TestCase):
    """Tests for zoya.ai.llm module."""

    def setUp(self):
        self.responses = {
            "hello": "Hi there!",
            "weather": "The weather is sunny.",
        }
        self.provider = MockProvider(responses=self.responses, model="test-model")

    def test_mock_provider_chat_returns_llm_response(self):
        result = self.provider.chat([{"role": "user", "content": "hello world"}])
        self.assertIsInstance(result, dict)
        self.assertIn("content", result)
        self.assertIn("usage", result)
        self.assertIn("model", result)
        self.assertEqual(result["content"], "Hi there!")
        self.assertEqual(result["model"], "test-model")

    def test_mock_provider_chat_usage_structure(self):
        result = self.provider.chat([{"role": "user", "content": "hello"}])
        usage = result["usage"]
        self.assertIn("prompt_tokens", usage)
        self.assertIn("completion_tokens", usage)
        self.assertIn("total_tokens", usage)
        self.assertEqual(
            usage["total_tokens"],
            usage["prompt_tokens"] + usage["completion_tokens"],
        )

    def test_mock_provider_substring_matching(self):
        result = self.provider.chat(
            [{"role": "user", "content": "tell me about the weather today"}]
        )
        self.assertEqual(result["content"], "The weather is sunny.")

    def test_mock_provider_fallback_response(self):
        result = self.provider.chat(
            [{"role": "user", "content": "something completely different"}]
        )
        self.assertIn("Mock response to:", result["content"])

    def test_mock_provider_empty_messages(self):
        result = self.provider.chat([])
        self.assertIn("Mock response to:", result["content"])

    def test_mock_provider_stream(self):
        chunks = list(self.provider.stream([{"role": "user", "content": "hello"}]))
        self.assertTrue(len(chunks) > 0)
        combined = "".join(chunks)
        self.assertEqual(combined.strip(), "Hi there!")

    def test_mock_provider_count_tokens(self):
        count = self.provider.count_tokens("hello world this is a test")
        self.assertIsInstance(count, int)
        self.assertGreater(count, 0)

    def test_create_provider_returns_mock(self):
        provider = create_provider("mock", responses={"test": "ok"})
        self.assertIsInstance(provider, MockProvider)
        result = provider.chat([{"role": "user", "content": "test"}])
        self.assertEqual(result["content"], "ok")

    def test_create_provider_invalid_name(self):
        with self.assertRaises(LLMError) as ctx:
            create_provider("nonexistent")
        self.assertIn("Unknown provider", str(ctx.exception))

    def test_create_provider_openai_no_key(self):
        with self.assertRaises(LLMError) as ctx:
            create_provider("openai")
        self.assertIn("API key", str(ctx.exception))

    def test_create_provider_anthropic_no_key(self):
        with self.assertRaises(LLMError) as ctx:
            create_provider("anthropic")
        self.assertIn("API key", str(ctx.exception))

    def test_llm_error_is_exception(self):
        self.assertTrue(issubclass(LLMError, Exception))

    def test_mock_provider_empty_responses(self):
        provider = MockProvider()
        result = provider.chat([{"role": "user", "content": "hello"}])
        self.assertIn("Mock response to:", result["content"])

    def test_mock_provider_custom_model(self):
        provider = MockProvider(model="custom-v1")
        self.assertEqual(provider.model, "custom-v1")
        result = provider.chat([{"role": "user", "content": "hello"}])
        self.assertEqual(result["model"], "custom-v1")


# ============================================================================
# Tools Tests
# ============================================================================


class TestTools(unittest.TestCase):
    """Tests for zoya.ai.tools module."""

    def setUp(self):
        self.registry = ToolRegistryBase()

    def test_tool_registry_register_and_get(self):
        tool = Calculator()
        self.registry.register(tool)
        retrieved = self.registry.get("calculator")
        self.assertIs(retrieved, tool)

    def test_tool_registry_list(self):
        self.registry.register(Calculator())
        self.registry.register(WebSearchTool())
        tools = self.registry.list()
        self.assertEqual(len(tools), 2)

    def test_tool_registry_duplicate_raises_error(self):
        self.registry.register(Calculator())
        with self.assertRaises(ToolError) as ctx:
            self.registry.register(Calculator())
        self.assertIn("already registered", str(ctx.exception))

    def test_tool_registry_get_nonexistent(self):
        with self.assertRaises(ToolError) as ctx:
            self.registry.get("nonexistent")
        self.assertIn("not found", str(ctx.exception))

    def test_tool_registry_execute(self):
        self.registry.register(Calculator())
        result = self.registry.execute("calculator", expression="2 + 3")
        parsed = json.loads(result)
        self.assertEqual(parsed["result"], 5)

    def test_calculator_basic_arithmetic(self):
        calc = Calculator()
        result = json.loads(calc.execute(expression="2 + 3 * 4"))
        self.assertEqual(result["result"], 14)

    def test_calculator_math_functions(self):
        calc = Calculator()
        result = json.loads(calc.execute(expression="sin(pi/2)"))
        self.assertAlmostEqual(result["result"], 1.0)

    def test_calculator_rejects_imports(self):
        calc = Calculator()
        with self.assertRaises(ToolError) as ctx:
            calc.execute(expression="__import__('os')")
        self.assertIn("not allowed", str(ctx.exception))

    def test_calculator_rejects_builtins(self):
        calc = Calculator()
        with self.assertRaises(ToolError):
            calc.execute(expression="[x for x in [1, 2]]")

    def test_calculator_rejects_attributes(self):
        calc = Calculator()
        with self.assertRaises(ToolError):
            calc.execute(expression="(2).__class__")

    def test_web_search_tool_returns_mock(self):
        search = WebSearchTool()
        result = json.loads(search.execute(query="test query"))
        self.assertIn("results", result)
        self.assertEqual(len(result["results"]), 1)
        self.assertIn("test query", result["results"][0]["title"])

    def test_web_search_tool_custom_func(self):
        def fake_search(q):
            return {"results": [{"title": q.upper()}]}

        search = WebSearchTool(search_func=fake_search)
        result = json.loads(search.execute(query="hello"))
        self.assertEqual(result["results"][0]["title"], "HELLO")

    def test_web_search_tool_custom_func_error(self):
        def broken(q):
            raise ValueError("API down")

        search = WebSearchTool(search_func=broken)
        with self.assertRaises(ToolError):
            search.execute(query="test")

    def test_file_read_tool_reads_file(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as f:
            f.write("file content")
            f.flush()
            filepath = f.name
        try:
            reader = FileReadTool()
            content = reader.execute(path=filepath)
            self.assertEqual(content, "file content")
        finally:
            os.unlink(filepath)

    def test_file_read_tool_file_not_found(self):
        reader = FileReadTool()
        with self.assertRaises(ToolError) as ctx:
            reader.execute(path=r"C:\nonexistent_file_xyz.txt")
        self.assertIn("not found", str(ctx.exception))

    def test_file_read_tool_directory_rejected(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            reader = FileReadTool()
            with self.assertRaises(ToolError) as ctx:
                reader.execute(path=tmpdir)
            self.assertIn("not a file", str(ctx.exception))

    def test_file_read_tool_path_traversal(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            reader = FileReadTool(allowed_base_path=tmpdir)
            with self.assertRaises(ToolError) as ctx:
                reader.execute(path=os.path.join(tmpdir, "..", "outside.txt"))
            self.assertIn("outside the allowed base", str(ctx.exception))

    def test_file_write_tool_writes_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test.txt")
            writer = FileWriteTool()
            result = json.loads(writer.execute(path=filepath, content="hello world"))
            self.assertEqual(result["status"], "written")
            self.assertEqual(result["bytes"], 11)
            with open(filepath, encoding="utf-8") as f:
                self.assertEqual(f.read(), "hello world")

    def test_file_write_tool_creates_directories(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "sub", "nested", "test.txt")
            writer = FileWriteTool()
            result = json.loads(writer.execute(path=filepath, content="nested"))
            self.assertEqual(result["status"], "written")
            self.assertTrue(os.path.exists(filepath))

    def test_file_write_tool_path_traversal(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            writer = FileWriteTool(allowed_base_path=tmpdir)
            with self.assertRaises(ToolError) as ctx:
                writer.execute(
                    path=os.path.join(tmpdir, "..", "bad.txt"),
                    content="evil",
                )
            self.assertIn("outside the allowed base", str(ctx.exception))

    def test_python_execute_tool_simple_code(self):
        executor = PythonExecuteTool()
        result = executor.execute(code="print('hello from python')")
        self.assertIn("hello from python", result)

    def test_python_execute_tool_returns_output(self):
        executor = PythonExecuteTool()
        result = executor.execute(code="x = 2 + 2\nprint(f'result={x}')")
        self.assertIn("result=4", result)

    def test_python_execute_tool_no_output(self):
        executor = PythonExecuteTool()
        result = json.loads(executor.execute(code="x = 42"))
        self.assertIn("Code executed successfully", result["result"])

    def test_python_execute_tool_blocks_os_import(self):
        executor = PythonExecuteTool()
        with self.assertRaises(ToolError) as ctx:
            executor.execute(code="import os\nprint('nope')")
        self.assertIn("not allowed", str(ctx.exception))

    def test_python_execute_tool_blocks_subprocess_import(self):
        executor = PythonExecuteTool()
        with self.assertRaises(ToolError) as ctx:
            executor.execute(code="import subprocess; subprocess.run('ls')")
        self.assertIn("not allowed", str(ctx.exception))

    def test_python_execute_tool_blocks_from_import(self):
        executor = PythonExecuteTool()
        with self.assertRaises(ToolError):
            executor.execute(code="from os import path")

    def test_python_execute_tool_syntax_error(self):
        executor = PythonExecuteTool()
        with self.assertRaises(ToolError) as ctx:
            executor.execute(code="this is not valid python @@")
        self.assertIn("Invalid Python syntax", str(ctx.exception))

    def test_python_execute_tool_timeout_handling(self):
        executor = PythonExecuteTool()
        result = executor.execute(code="print('ok')", timeout=1)
        self.assertIn("ok", result)

    def test_shell_tool_disabled(self):
        shell = ShellTool()
        with self.assertRaises(ToolError) as ctx:
            shell.execute(command="echo test")
        self.assertIn("disabled", str(ctx.exception))

    def test_tool_decorator_creates_tool(self):
        @tool(name="greet", description="Greets someone")
        def greet(name: str):
            """Greet a person by name."""
            return f"Hello, {name}!"

        self.assertIsInstance(greet, ToolBase)
        self.assertEqual(greet.name, "greet")
        self.assertEqual(greet.description, "Greets someone")
        result = greet.execute(name="World")
        self.assertEqual(result, "Hello, World!")

    def test_tool_decorator_default_name(self):
        @tool()
        def my_custom_function(x: int):
            return x * 2

        self.assertEqual(my_custom_function.name, "my_custom_function")

    def test_tool_to_openai_format(self):
        calc = Calculator()
        fmt = calc.to_openai_format()
        self.assertEqual(fmt["type"], "function")
        self.assertEqual(fmt["function"]["name"], "calculator")
        self.assertIn("parameters", fmt["function"])

    def test_tool_to_anthropic_format(self):
        calc = Calculator()
        fmt = calc.to_anthropic_format()
        self.assertEqual(fmt["name"], "calculator")
        self.assertIn("input_schema", fmt)

    def test_registry_to_openai_tools(self):
        self.registry.register(Calculator())
        self.registry.register(WebSearchTool())
        tools = self.registry.to_openai_tools()
        self.assertEqual(len(tools), 2)
        names = [t["function"]["name"] for t in tools]
        self.assertIn("calculator", names)
        self.assertIn("web_search", names)

    def test_registry_to_anthropic_tools(self):
        self.registry.register(Calculator())
        tools = self.registry.to_anthropic_tools()
        self.assertEqual(len(tools), 1)
        self.assertEqual(tools[0]["name"], "calculator")

    def test_tool_class_default_name(self):
        """Tool subclasses inherit name/description from class attributes."""
        calc = Calculator()
        self.assertEqual(calc.name, "calculator")

    def test_tool_registry_execute_unknown_tool(self):
        with self.assertRaises(ToolError):
            self.registry.execute("unknown", foo=1)


# ============================================================================
# Memory Tests
# ============================================================================


class TestMemory(unittest.TestCase):
    """Tests for zoya.ai.memory module."""

    def setUp(self):
        self.conv = ConversationMemory()
        self.semantic = SemanticMemory()

    # --- ConversationMemory ---

    def test_conversation_add_and_get_history(self):
        self.conv.add("user", "Hello")
        self.conv.add("assistant", "Hi there")
        history = self.conv.get_history()
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["role"], "user")
        self.assertEqual(history[0]["content"], "Hello")
        self.assertEqual(history[1]["role"], "assistant")
        self.assertEqual(history[1]["content"], "Hi there")

    def test_conversation_get_recent(self):
        self.conv.add("user", "msg1")
        self.conv.add("user", "msg2")
        self.conv.add("user", "msg3")
        recent = self.conv.get_recent(2)
        self.assertEqual(len(recent), 2)
        self.assertEqual(recent[0]["content"], "msg2")
        self.assertEqual(recent[1]["content"], "msg3")

    def test_conversation_get_recent_invalid(self):
        with self.assertRaises(MemoryError):
            self.conv.get_recent(0)

    def test_conversation_clear(self):
        self.conv.add("user", "Hello")
        self.conv.clear()
        self.assertEqual(len(self.conv.get_history()), 0)

    def test_conversation_count_tokens(self):
        self.conv.add("user", "hello world")
        tokens = self.conv.count_tokens()
        self.assertIsInstance(tokens, int)
        self.assertGreater(tokens, 0)

    def test_conversation_add_with_metadata(self):
        self.conv.add("user", "test", metadata={"source": "test_suite"})
        history = self.conv.get_history()
        self.assertEqual(history[0]["metadata"]["source"], "test_suite")

    def test_conversation_set_max_tokens_triggers_summarization(self):
        self.conv.add("user", "A" * 200)
        self.conv.add("assistant", "B" * 200)
        self.conv.set_max_tokens(10)
        history = self.conv.get_history()
        self.assertGreaterEqual(len(history), 1)

    def test_conversation_set_max_tokens_negative(self):
        with self.assertRaises(MemoryError):
            self.conv.set_max_tokens(-1)

    def test_conversation_summarize_empty(self):
        self.conv.summarize()
        self.assertEqual(len(self.conv.get_history()), 0)

    def test_conversation_summarize_single_message(self):
        self.conv.add("user", "only one")
        self.conv.summarize()
        self.assertEqual(len(self.conv.get_history()), 1)

    def test_conversation_get_history_returns_copy(self):
        self.conv.add("user", "msg")
        history = self.conv.get_history()
        history.append({"role": "system", "content": "injected"})
        self.assertEqual(len(self.conv.get_history()), 1)

    # --- SemanticMemory ---

    def test_semantic_store_and_retrieve(self):
        self.semantic.store("hello world", "greeting_value")
        results = self.semantic.retrieve("hello", k=5)
        self.assertTrue(len(results) >= 1)
        self.assertEqual(results[0]["key"], "hello world")
        self.assertEqual(results[0]["value"], "greeting_value")

    def test_semantic_retrieve_returns_score(self):
        self.semantic.store("python programming", "code")
        results = self.semantic.retrieve("python", k=5)
        self.assertGreater(results[0]["score"], 0)

    def test_semantic_get_existing(self):
        self.semantic.store("key1", "value1")
        val = self.semantic.get("key1")
        self.assertEqual(val, "value1")

    def test_semantic_get_nonexistent(self):
        with self.assertRaises(MemoryError) as ctx:
            self.semantic.get("no_such_key")
        self.assertIn("not found", str(ctx.exception))

    def test_semantic_delete(self):
        self.semantic.store("todelete", "val")
        self.semantic.delete("todelete")
        self.assertEqual(len(self.semantic.list()), 0)

    def test_semantic_delete_nonexistent(self):
        with self.assertRaises(MemoryError):
            self.semantic.delete("no_such_key")

    def test_semantic_list(self):
        self.semantic.store("a", 1)
        self.semantic.store("b", 2)
        keys = self.semantic.list()
        self.assertIn("a", keys)
        self.assertIn("b", keys)

    def test_semantic_clear(self):
        self.semantic.store("x", 100)
        self.semantic.clear()
        self.assertEqual(len(self.semantic.list()), 0)

    def test_semantic_store_empty_key(self):
        with self.assertRaises(MemoryError):
            self.semantic.store("", "val")

    def test_semantic_retrieve_from_empty(self):
        results = self.semantic.retrieve("anything")
        self.assertEqual(results, [])

    def test_semantic_retrieve_invalid_k(self):
        self.semantic.store("something", "value")
        with self.assertRaises(MemoryError):
            self.semantic.retrieve("test", k=0)

    def test_semantic_store_with_metadata(self):
        self.semantic.store("key", "val", metadata={"type": "test"})
        results = self.semantic.retrieve("key")
        self.assertEqual(results[0]["metadata"]["type"], "test")

    # --- AgentMemory ---

    def test_agent_memory_combines_conversation_and_knowledge(self):
        from zoya.ai.memory import AgentMemory as SemanticAgentMemory

        am = SemanticAgentMemory()
        am.conversation.add("user", "question")
        am.knowledge.store("fact", "data")
        self.assertEqual(len(am.conversation.get_history()), 1)
        self.assertEqual(len(am.knowledge.list()), 1)

    def test_agent_memory_save_and_load(self):
        from zoya.ai.memory import AgentMemory as SemanticAgentMemory

        am = SemanticAgentMemory()
        am.conversation.add("user", "hello")
        am.conversation.add("assistant", "hi")
        am.knowledge.store("color", "blue")
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            filepath = f.name
        try:
            am.save(filepath)
            am2 = SemanticAgentMemory()
            am2.load(filepath)
            conv_hist = am2.conversation.get_history()
            self.assertEqual(len(conv_hist), 2)
            self.assertEqual(conv_hist[0]["content"], "hello")
            self.assertEqual(conv_hist[1]["content"], "hi")
            self.assertEqual(am2.knowledge.get("color"), "blue")
        finally:
            os.unlink(filepath)


# ============================================================================
# Embeddings Tests
# ============================================================================


class TestEmbeddings(unittest.TestCase):
    """Tests for zoya.ai.embeddings module."""

    def test_cosine_similarity_identical(self):
        vec = [1.0, 2.0, 3.0]
        sim = cosine_similarity(vec, vec)
        self.assertAlmostEqual(sim, 1.0)

    def test_cosine_similarity_orthogonal(self):
        a = [1.0, 0.0]
        b = [0.0, 1.0]
        sim = cosine_similarity(a, b)
        self.assertAlmostEqual(sim, 0.0)

    def test_cosine_similarity_zero_vectors(self):
        a = [0.0, 0.0, 0.0]
        b = [1.0, 0.0, 0.0]
        sim = cosine_similarity(a, b)
        self.assertEqual(sim, 0.0)

    def test_cosine_similarity_different_dimensions(self):
        with self.assertRaises(EmbeddingError) as ctx:
            cosine_similarity([1.0, 2.0], [1.0, 2.0, 3.0])
        self.assertIn("same dimension", str(ctx.exception))

    def test_cosine_similarity_same_direction(self):
        a = [2.0, 4.0, 6.0]
        b = [1.0, 2.0, 3.0]
        sim = cosine_similarity(a, b)
        self.assertAlmostEqual(sim, 1.0)

    def test_simple_tokenize_basic(self):
        tokens = simple_tokenize("Hello World! This is a TEST.")
        self.assertEqual(tokens, ["hello", "world", "this", "is", "a", "test"])

    def test_simple_tokenize_non_string(self):
        with self.assertRaises(EmbeddingError):
            simple_tokenize(123)

    def test_simple_tokenize_empty_string(self):
        tokens = simple_tokenize("")
        self.assertEqual(tokens, [])

    def test_simple_tokenize_numbers_and_symbols(self):
        tokens = simple_tokenize("item_123 v2.0")
        self.assertEqual(tokens, ["item", "v"])

    def test_tfidf_vectorizer_fit_and_transform(self):
        vectorizer = TFIDFVectorizer()
        vectorizer.fit(["hello world", "goodbye world"])
        vec = vectorizer.transform("hello")
        self.assertIsInstance(vec, list)
        self.assertTrue(all(isinstance(v, float) for v in vec))
        self.assertEqual(len(vec), vectorizer.vocabulary_size())

    def test_tfidf_vectorizer_transform_before_fit(self):
        vectorizer = TFIDFVectorizer()
        with self.assertRaises(EmbeddingError):
            vectorizer.transform("test")

    def test_tfidf_vectorizer_fit_empty(self):
        vectorizer = TFIDFVectorizer()
        with self.assertRaises(EmbeddingError):
            vectorizer.fit([])

    def test_tfidf_vectorizer_vocabulary_size_zero(self):
        vectorizer = TFIDFVectorizer()
        self.assertEqual(vectorizer.vocabulary_size(), 0)

    def test_text_embedding_embed_returns_correct_dimension(self):
        embedder = TextEmbedding(dimension=10)
        embedder.fit(["cat dog", "bird fish"])
        vec = embedder.embed("cat")
        self.assertEqual(len(vec), 10)

    def test_text_embedding_embed_before_fit(self):
        embedder = TextEmbedding()
        with self.assertRaises(EmbeddingError):
            embedder.embed("test")

    def test_text_embedding_similarity(self):
        embedder = TextEmbedding(dimension=16)
        embedder.fit(["python is a programming language", "cooking recipes and food"])
        sim_same = embedder.similarity("python programming", "programming language")
        sim_diff = embedder.similarity("python programming", "cooking food")
        self.assertGreater(sim_same, sim_diff)

    def test_text_embedding_batch_embed(self):
        embedder = TextEmbedding(dimension=8)
        embedder.fit(["one", "two", "three"])
        vectors = embedder.batch_embed(["one", "two"])
        self.assertEqual(len(vectors), 2)
        self.assertEqual(len(vectors[0]), 8)

    def test_text_embedding_invalid_dimension(self):
        with self.assertRaises(EmbeddingError):
            TextEmbedding(dimension=0)

    def test_text_embedding_truncates_long_vectors(self):
        embedder = TextEmbedding(dimension=2)
        embedder.fit(["hello world foo bar baz"])
        vec = embedder.embed("hello world foo bar baz")
        self.assertEqual(len(vec), 2)

    def test_tfidf_vectorizer_fit_deterministic_vocab(self):
        v1 = TFIDFVectorizer()
        v2 = TFIDFVectorizer()
        v1.fit(["alpha beta"])
        v2.fit(["alpha beta"])
        self.assertEqual(v1._vocab, v2._vocab)


# ============================================================================
# Agent Tests
# ============================================================================


class TestAgent(unittest.TestCase):
    """Tests for zoya.ai.agent module."""

    def test_create_agent_returns_agent(self):
        agent = create_agent(provider=lambda p, **kw: "Answer: ok")
        self.assertIsInstance(agent, Agent)

    def test_agent_no_provider_raises_error(self):
        with self.assertRaises(AgentError):
            Agent({"provider": None})

    def test_agent_run_returns_answer(self):
        agent = create_agent(provider=lambda p, **kw: "Answer: Hello world!")
        result = agent.run("Say hello")
        self.assertEqual(result, "Hello world!")

    def test_agent_run_with_answer_in_body(self):
        agent = create_agent(
            provider=lambda p, **kw: "Here is what I think.\nAnswer: Final answer"
        )
        result = agent.run("Do something")
        self.assertEqual(result, "Final answer")

    def test_agent_reset_clears_state(self):
        agent = create_agent(provider=lambda p, **kw: "Answer: some answer")
        agent.run("First task")
        self.assertEqual(len(agent.memory.get_history()), 2)
        agent.reset()
        self.assertEqual(len(agent.memory.get_history()), 0)

    def test_agent_add_tool(self):
        agent = create_agent(provider=lambda p, **kw: "Answer: ok")
        tool = AgentTool("reverse", "Reverse a string", func=lambda s: s[::-1])
        agent.add_tool(tool)
        self.assertIsNotNone(agent.tools.get("reverse"))

    def test_agent_add_tool_invalid(self):
        agent = create_agent(provider=lambda p, **kw: "Answer: ok")
        with self.assertRaises(AgentError):
            agent.add_tool("not a tool")

    def test_agent_run_uses_tool(self):
        responses = iter(
            [
                'Action: reverse\nAction Input: {"s": "hello"}',
                "Answer: The reversed string is olleh",
            ]
        )

        def mock_provider(prompt, **kw):
            return next(responses)

        tool = AgentTool("reverse", "Reverse", func=lambda s: s[::-1])
        registry = AgentToolRegistry()
        registry.register(tool)
        agent = create_agent(provider=mock_provider, tools=registry)
        result = agent.run("Reverse hello")
        self.assertEqual(result, "The reversed string is olleh")

    def test_agent_run_unknown_tool(self):
        responses = iter(
            [
                'Action: nonexistent_tool\nAction Input: {"x": "1"}',
                "Answer: Error handled",
            ]
        )

        def mock_provider(prompt, **kw):
            return next(responses)

        agent = create_agent(provider=mock_provider)
        result = agent.run("Do something")
        self.assertEqual(result, "Error handled")

    def test_agent_run_max_iterations(self):
        def always_tool(prompt, **kw):
            return 'Action: calculator\nAction Input: {"expression": "1+1"}'

        agent = create_agent(provider=always_tool, max_iterations=2)
        result = agent.run("Loop")
        self.assertIn("Max iterations", result)

    def test_agent_parse_tool_call_action_format(self):
        agent = create_agent(provider=lambda p, **kw: "Answer: x")
        result = agent._parse_tool_call(
            'Action: calculator\nAction Input: {"expression": "2+2"}'
        )
        self.assertIsNotNone(result)
        name, args = result
        self.assertEqual(name, "calculator")
        self.assertEqual(args, {"expression": "2+2"})

    def test_agent_parse_tool_call_json_format(self):
        agent = create_agent(provider=lambda p, **kw: "Answer: x")
        result = agent._parse_tool_call(
            '{"function": "search", "arguments": {"q": "test"}}'
        )
        self.assertIsNotNone(result)
        name, args = result
        self.assertEqual(name, "search")
        self.assertEqual(args, {"q": "test"})

    def test_agent_parse_tool_call_function_call_format(self):
        agent = create_agent(provider=lambda p, **kw: "Answer: x")
        result = agent._parse_tool_call(
            'function_call: "search"\narguments: {"q": "test"}'
        )
        self.assertIsNotNone(result)
        name, args = result
        self.assertEqual(name, "search")

    def test_agent_parse_tool_call_no_match(self):
        agent = create_agent(provider=lambda p, **kw: "Answer: x")
        result = agent._parse_tool_call("Just a plain response with no tool call")
        self.assertIsNone(result)

    def test_agent_parse_tool_call_with_backtick_input(self):
        agent = create_agent(provider=lambda p, **kw: "Answer: x")
        result = agent._parse_tool_call(
            'Action: calculator\nAction Input: `{"expression": "2+2"}`'
        )
        self.assertIsNotNone(result)
        name, args = result
        self.assertEqual(name, "calculator")
        self.assertEqual(args, {"expression": "2+2"})

    def test_planning_agent_create_plan(self):
        config = {
            "provider": lambda p, **kw: "Step 1: Research the topic\nStep 2: Write report",
        }
        agent = PlanningAgent(config)
        steps = agent._create_plan("Write about AI")
        self.assertEqual(len(steps), 2)
        self.assertIn("Research", steps[0])
        self.assertIn("Write", steps[1])

    def test_planning_agent_create_plan_no_match(self):
        config = {
            "provider": lambda p, **kw: "# only comments\n# no real steps",
        }
        agent = PlanningAgent(config)
        steps = agent._create_plan("Simple task")
        self.assertEqual(len(steps), 1)
        self.assertEqual(steps[0], "Simple task")

    def test_planning_agent_inherits_from_agent(self):
        self.assertTrue(issubclass(PlanningAgent, Agent))

    def test_agent_memory_get_history(self):
        agent = create_agent(provider=lambda p, **kw: "Answer: ok")
        agent.run("test")
        history = agent.memory.get_history()
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["role"], "user")
        self.assertEqual(history[0]["content"], "test")
        self.assertEqual(history[1]["role"], "assistant")
        self.assertEqual(history[1]["content"], "ok")

    def test_agent_run_no_action_returns_raw(self):
        agent = create_agent(provider=lambda p, **kw: "Just a friendly chat")
        result = agent.run("Hello")
        self.assertEqual(result, "Just a friendly chat")

    def test_create_agent_custom_system_prompt(self):
        agent = create_agent(
            provider=lambda p, **kw: "Answer: ok",
            system_prompt="You are a bot.",
        )
        self.assertEqual(agent.system_prompt, "You are a bot.")


# ============================================================================
# RAG Tests
# ============================================================================


class TestRAG(unittest.TestCase):
    """Tests for zoya.ai.rag module."""

    # --- DocumentChunker ---

    def test_chunker_splits_text(self):
        chunker = DocumentChunker(chunk_size=200, overlap=20)
        text = "This is the first sentence. This is the second sentence. " * 10
        chunks = chunker.chunk(text)
        self.assertGreater(len(chunks), 1)
        for doc in chunks:
            self.assertIn("text", doc)
            self.assertIn("id", doc)
            self.assertIn("metadata", doc)

    def test_chunker_respects_chunk_boundaries(self):
        chunker = DocumentChunker(chunk_size=50, overlap=10)
        text = "One. Two. Three. Four. Five. Six. Seven. Eight. Nine. Ten."
        chunks = chunker.chunk(text)
        for doc in chunks:
            self.assertLessEqual(len(doc["text"]), 70)

    def test_chunker_empty_text(self):
        chunker = DocumentChunker()
        chunks = chunker.chunk("")
        self.assertEqual(chunks, [])

    def test_chunker_whitespace_only(self):
        chunker = DocumentChunker()
        chunks = chunker.chunk("   \n\n  ")
        self.assertEqual(chunks, [])

    def test_chunker_invalid_chunk_size(self):
        with self.assertRaises(RAGError):
            DocumentChunker(chunk_size=0)

    def test_chunker_invalid_overlap(self):
        with self.assertRaises(RAGError):
            DocumentChunker(chunk_size=10, overlap=-1)

    def test_chunker_overlap_gte_chunk_size(self):
        with self.assertRaises(RAGError):
            DocumentChunker(chunk_size=10, overlap=10)

    def test_chunker_chunk_documents(self):
        chunker = DocumentChunker(chunk_size=500, overlap=50)
        docs = [
            (
                "This is the first document with enough text. It has multiple sentences. Here is another one."
                * 3,
                {"source": "doc1"},
            ),
            (
                "This is the second document. It also has some content to chunk." * 3,
                {"source": "doc2"},
            ),
        ]
        chunks = chunker.chunk_documents(docs)
        self.assertGreater(len(chunks), 1)

    def test_chunker_preserves_metadata(self):
        chunker = DocumentChunker(chunk_size=500, overlap=50)
        text = "Sentence one. Sentence two. Sentence three. " * 5
        chunks = chunker.chunk(text, {"source": "test_doc", "author": "tester"})
        for doc in chunks:
            self.assertEqual(doc["metadata"]["source"], "test_doc")
            self.assertEqual(doc["metadata"]["author"], "tester")

    # --- RAGIndex ---

    def test_index_add_document_returns_id(self):
        index = RAGIndex()
        doc_id = index.add_document(
            "This is a test document about artificial intelligence."
        )
        self.assertIsInstance(doc_id, str)
        self.assertTrue(len(doc_id) > 0)

    def test_index_search_returns_results(self):
        index = RAGIndex()
        index.add_document(
            "Python is a programming language used for machine learning."
        )
        results = index.search("python programming", k=5)
        self.assertGreaterEqual(len(results), 1)
        doc, score = results[0]
        self.assertIn("text", doc)
        self.assertIsInstance(score, float)

    def test_index_search_returns_results_with_positive_score(self):
        index = RAGIndex()
        index.add_document("Machine learning and deep learning are AI subfields.")
        results = index.search("machine learning", k=5)
        self.assertGreaterEqual(len(results), 1)
        doc, score = results[0]
        self.assertGreater(score, 0)

    def test_index_add_documents_batch(self):
        index = RAGIndex()
        docs = [
            Document(
                text="Document one about cats.", metadata={"source": "a"}, id="id1"
            ),
            Document(
                text="Document two about dogs.", metadata={"source": "b"}, id="id2"
            ),
        ]
        index.add_documents(docs)
        self.assertEqual(index.count(), 2)

    def test_index_clear_and_count(self):
        index = RAGIndex()
        index.add_document("Text one")
        index.add_document("Text two")
        self.assertEqual(index.count(), 2)
        index.clear()
        self.assertEqual(index.count(), 0)

    def test_index_remove_document(self):
        index = RAGIndex()
        doc_id = index.add_document("Something to remove")
        self.assertEqual(index.count(), 1)
        index.remove(doc_id)
        self.assertEqual(index.count(), 0)

    def test_index_add_empty_text_raises_error(self):
        index = RAGIndex()
        with self.assertRaises(RAGError):
            index.add_document("")

    def test_index_add_whitespace_text_raises_error(self):
        index = RAGIndex()
        with self.assertRaises(RAGError):
            index.add_document("   ")

    def test_index_search_empty_query_raises_error(self):
        index = RAGIndex()
        index.add_document("Some text")
        with self.assertRaises(RAGError):
            index.search("")

    def test_index_search_empty_index(self):
        index = RAGIndex()
        results = index.search("anything", k=5)
        self.assertEqual(results, [])

    def test_index_search_invalid_k(self):
        index = RAGIndex()
        index.add_document("Some text")
        with self.assertRaises(RAGError):
            index.search("query", k=0)

    def test_index_add_documents_duplicate_id_handling(self):
        index = RAGIndex()
        docs = [
            Document(text="First doc", metadata={}, id="dup"),
            Document(text="Second doc", metadata={}, id="dup"),
        ]
        index.add_documents(docs)
        self.assertEqual(index.count(), 2)

    def test_index_add_documents_empty_list(self):
        index = RAGIndex()
        index.add_documents([])
        self.assertEqual(index.count(), 0)

    def test_index_add_documents_skips_invalid(self):
        index = RAGIndex()
        docs = [
            Document(text="Valid doc", metadata={}),
            Document(text="", metadata={}),
            Document(text="  ", metadata={}),
        ]
        index.add_documents(docs)
        self.assertEqual(index.count(), 1)

    # --- RAGRetriever ---

    def test_retriever_query_returns_prompt(self):
        index = RAGIndex()
        index.add_document("Artificial intelligence transforms industries.")
        retriever = RAGRetriever(index)
        prompt = retriever.query("Tell me about AI", k=5)
        self.assertIsInstance(prompt, str)
        self.assertIn("Artificial intelligence", prompt)
        self.assertIn("Tell me about AI", prompt)

    def test_retriever_query_with_sources(self):
        index = RAGIndex()
        index.add_document("Relevant content about machine learning.")
        retriever = RAGRetriever(index)
        prompt, sources = retriever.query_with_sources("machine learning", k=5)
        self.assertIsInstance(prompt, str)
        self.assertIsInstance(sources, list)
        self.assertGreaterEqual(len(sources), 1)
        self.assertIn("text", sources[0])

    def test_retriever_format_context(self):
        index = RAGIndex()
        index.add_document("Sample document text.", metadata={"source": "test"})
        results = index.search("sample", k=5)
        retriever = RAGRetriever(index)
        formatted = retriever.format_context(results)
        self.assertIn("Sample document text.", formatted)
        self.assertIn("test", formatted)
        self.assertIn("relevance:", formatted)

    def test_retriever_format_context_empty(self):
        index = RAGIndex()
        retriever = RAGRetriever(index)
        formatted = retriever.format_context([])
        self.assertEqual(formatted, "No relevant documents found.")

    def test_retriever_invalid_index(self):
        with self.assertRaises(RAGError):
            RAGRetriever("not an index")

    def test_retriever_custom_system_prompt(self):
        index = RAGIndex()
        index.add_document("Some content.")
        retriever = RAGRetriever(index, system_prompt="Custom prompt here.")
        prompt = retriever.query("test", k=5)
        self.assertIn("Custom prompt here.", prompt)

    def test_retriever_query_empty_index(self):
        index = RAGIndex()
        retriever = RAGRetriever(index)
        prompt = retriever.query("anything", k=5)
        self.assertIn("No relevant documents found.", prompt)

    def test_retriever_query_with_sources_empty(self):
        index = RAGIndex()
        retriever = RAGRetriever(index)
        prompt, sources = retriever.query_with_sources("anything", k=5)
        self.assertEqual(sources, [])


if __name__ == "__main__":
    unittest.main()
