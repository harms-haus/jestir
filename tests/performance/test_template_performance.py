"""Performance tests for template testing functionality."""

import os
import tempfile
import time

from jestir.services.template_debugger import TemplateDebugger
from jestir.services.template_loader import TemplateLoader


class TestTemplatePerformance:
    """Test template system performance characteristics."""

    def setup_method(self):
        """Set up test fixtures."""
        self.template_loader = TemplateLoader()
        self.template_debugger = TemplateDebugger(self.template_loader)
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_template_loading_performance(self):
        """Test template loading performance with various sizes."""
        # Test with different template sizes
        sizes = [100, 1000, 5000, 10000, 50000]  # characters

        for size in sizes:
            # Create template of specified size
            template_content = "Hello {{name}}! " * (size // 15)  # Approximate size
            template_path = os.path.join(self.temp_dir, f"template_{size}.txt")

            with open(template_path, "w") as f:
                f.write(template_content)

            # Measure loading time
            start_time = time.time()
            content = self.template_loader.load_template(template_path)
            loading_time = time.time() - start_time

            # Verify performance requirements
            assert loading_time < 0.1  # Should load in < 100ms
            assert len(content) >= size * 0.8  # Should load most content

            # Test caching performance (second load should be faster)
            start_time = time.time()
            cached_content = self.template_loader.load_template(template_path)
            cached_time = time.time() - start_time

            assert cached_time < loading_time  # Cached should be faster
            assert cached_content == content  # Content should be identical

    def test_template_rendering_performance(self):
        """Test template rendering performance with various complexities."""
        # Test with different variable counts
        variable_counts = [1, 10, 50, 100, 500]

        for var_count in variable_counts:
            # Create template with specified variable count
            template_parts = []
            context = {}

            for i in range(var_count):
                var_name = f"var_{i}"
                template_parts.append(f"{{{{{var_name}}}}}")
                context[var_name] = f"value_{i}"

            template_content = " ".join(template_parts)
            template_path = os.path.join(self.temp_dir, f"render_{var_count}.txt")

            with open(template_path, "w") as f:
                f.write(template_content)

            # Measure rendering time
            start_time = time.time()
            rendered = self.template_loader.render_template(template_path, context)
            rendering_time = time.time() - start_time

            # Verify performance requirements
            assert rendering_time < 0.5  # Should render in < 500ms
            assert "{{" not in rendered  # All variables should be resolved

            # Performance should scale reasonably
            if var_count <= 100:
                assert rendering_time < 0.1  # Small templates should be very fast

    def test_template_validation_performance(self):
        """Test template validation performance."""
        # Create a complex template
        template_content = "Hello {{name}}! " * 1000  # 1000 repetitions
        template_path = os.path.join(self.temp_dir, "validation_test.txt")

        with open(template_path, "w") as f:
            f.write(template_content)

        # Measure syntax validation time
        start_time = time.time()
        syntax_result = self.template_loader.validate_template_syntax(template_path)
        syntax_time = time.time() - start_time

        assert syntax_time < 0.2  # Should validate in < 200ms
        assert syntax_result["valid"] is True
        assert syntax_result["variable_count"] == 1000

        # Measure context validation time
        context = {"name": "Alice"}
        start_time = time.time()
        context_result = self.template_loader.validate_template_with_context(
            template_path, context,
        )
        context_time = time.time() - start_time

        assert context_time < 0.3  # Should validate in < 300ms
        assert context_result["valid"] is True

    def test_template_analysis_performance(self):
        """Test template analysis performance."""
        # Create a large, complex template
        template_content = "Hello {{name # protagonist name}}! " * 500
        template_content += "This is a {{genre # story genre}} story. " * 500
        template_content += "For {{age_appropriate # target age}} children. " * 500

        template_path = os.path.join(self.temp_dir, "analysis_test.txt")

        with open(template_path, "w") as f:
            f.write(template_content)

        # Measure analysis time
        start_time = time.time()
        analysis = self.template_debugger.analyze_template(template_path)
        analysis_time = time.time() - start_time

        assert analysis_time < 1.0  # Should analyze in < 1 second
        assert analysis.variable_count == 1500  # 3 variables * 500 repetitions
        assert analysis.complexity_score > 0
        assert analysis.analysis_time == analysis_time

    def test_template_debugging_performance(self):
        """Test template debugging performance."""
        # Create template with many variables
        template_parts = []
        context = {}

        for i in range(100):
            var_name = f"var_{i}"
            template_parts.append(f"{{{{{var_name} # variable {i}}}}}")
            context[var_name] = f"value_{i}"

        template_content = " ".join(template_parts)
        template_path = os.path.join(self.temp_dir, "debug_test.txt")

        with open(template_path, "w") as f:
            f.write(template_content)

        # Measure debugging time
        start_time = time.time()
        debug_result = self.template_debugger.debug_template_rendering(
            template_path, context,
        )
        debug_time = time.time() - start_time

        assert debug_time < 0.5  # Should debug in < 500ms
        assert debug_result["success"] is True
        assert debug_result["variables_used"] == 100
        assert debug_result["context_coverage"] == 1.0

    def test_template_comparison_performance(self):
        """Test template comparison performance."""
        # Create multiple templates
        template_paths = []
        for i in range(5):
            template_content = f"Template {i}: {{name}} {{genre}} {{age_appropriate}}" * 100
            template_path = os.path.join(self.temp_dir, f"compare_{i}.txt")

            with open(template_path, "w") as f:
                f.write(template_content)

            template_paths.append(template_path)

        # Measure comparison time
        start_time = time.time()
        comparison = self.template_debugger.compare_templates(template_paths)
        comparison_time = time.time() - start_time

        assert comparison_time < 2.0  # Should compare in < 2 seconds
        assert comparison["template_count"] == 5
        assert comparison["total_variables"] == 1500  # 5 templates * 300 variables each

    def test_memory_usage(self):
        """Test memory usage with large templates."""
        import gc

        import psutil

        # Get initial memory usage
        process = psutil.Process()
        initial_memory = process.memory_info().rss

        # Create and process many large templates
        for i in range(10):
            template_content = "Hello {{name}}! " * 1000  # Large template
            template_path = os.path.join(self.temp_dir, f"memory_{i}.txt")

            with open(template_path, "w") as f:
                f.write(template_content)

            # Load and render template
            content = self.template_loader.load_template(template_path)
            rendered = self.template_loader.render_template(template_path, {"name": "Alice"})

            # Analyze template
            analysis = self.template_debugger.analyze_template(template_path)

        # Force garbage collection
        gc.collect()

        # Check memory usage
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable (< 50MB for this test)
        assert memory_increase < 50 * 1024 * 1024  # 50MB

        # Clear cache and check memory again
        self.template_loader.clear_cache()
        self.template_debugger.clear_cache()
        gc.collect()

        cleared_memory = process.memory_info().rss
        memory_after_clear = cleared_memory - initial_memory

        # Memory should be significantly lower after clearing cache
        assert memory_after_clear < memory_increase * 0.5

    def test_concurrent_template_loading(self):
        """Test concurrent template loading performance."""
        import queue
        import threading

        # Create multiple templates
        template_paths = []
        for i in range(10):
            template_content = f"Template {i}: {{name}} {{genre}}" * 100
            template_path = os.path.join(self.temp_dir, f"concurrent_{i}.txt")

            with open(template_path, "w") as f:
                f.write(template_content)

            template_paths.append(template_path)

        # Load templates concurrently
        results = queue.Queue()

        def load_template(template_path):
            start_time = time.time()
            content = self.template_loader.load_template(template_path)
            loading_time = time.time() - start_time
            results.put((template_path, loading_time, len(content)))

        # Start threads
        threads = []
        start_time = time.time()

        for template_path in template_paths:
            thread = threading.Thread(target=load_template, args=(template_path,))
            thread.start()
            threads.append(thread)

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        total_time = time.time() - start_time

        # Verify all templates loaded successfully
        assert results.qsize() == 10

        # Check individual loading times
        while not results.empty():
            template_path, loading_time, content_length = results.get()
            assert loading_time < 0.1  # Each should load quickly
            assert content_length > 0  # Content should be loaded

        # Total time should be reasonable (concurrent loading)
        assert total_time < 1.0  # Should complete in < 1 second

    def test_template_caching_efficiency(self):
        """Test template caching efficiency."""
        # Create a template
        template_content = "Hello {{name}}! This is a {{genre}} story." * 100
        template_path = os.path.join(self.temp_dir, "cache_test.txt")

        with open(template_path, "w") as f:
            f.write(template_content)

        # First load (should be slower)
        start_time = time.time()
        content1 = self.template_loader.load_template(template_path)
        first_load_time = time.time() - start_time

        # Second load (should be faster due to caching)
        start_time = time.time()
        content2 = self.template_loader.load_template(template_path)
        second_load_time = time.time() - start_time

        # Verify caching works
        assert content1 == content2
        assert second_load_time < first_load_time * 0.5  # Should be significantly faster

        # Test cache hit ratio
        cache_hits = 0
        total_loads = 100

        for _ in range(total_loads):
            start_time = time.time()
            self.template_loader.load_template(template_path)
            load_time = time.time() - start_time

            if load_time < first_load_time * 0.1:  # Very fast = cache hit
                cache_hits += 1

        cache_hit_ratio = cache_hits / total_loads
        assert cache_hit_ratio > 0.9  # Should have >90% cache hit ratio

    def test_large_template_handling(self):
        """Test handling of very large templates."""
        # Create a very large template (1MB)
        large_content = "Hello {{name}}! " * 50000  # ~1MB
        template_path = os.path.join(self.temp_dir, "large_template.txt")

        with open(template_path, "w") as f:
            f.write(large_content)

        # Test loading performance
        start_time = time.time()
        content = self.template_loader.load_template(template_path)
        loading_time = time.time() - start_time

        assert loading_time < 2.0  # Should load in < 2 seconds
        assert len(content) > 1000000  # Should be > 1MB

        # Test rendering performance
        context = {"name": "Alice"}
        start_time = time.time()
        rendered = self.template_loader.render_template(template_path, context)
        rendering_time = time.time() - start_time

        assert rendering_time < 3.0  # Should render in < 3 seconds
        assert "Hello Alice!" in rendered
        assert "{{" not in rendered  # All variables should be resolved

        # Test analysis performance
        start_time = time.time()
        analysis = self.template_debugger.analyze_template(template_path)
        analysis_time = time.time() - start_time

        assert analysis_time < 5.0  # Should analyze in < 5 seconds
        assert analysis.variable_count == 50000
        assert analysis.complexity_score > 0
