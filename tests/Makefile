default: test

test-standard:
	pytest . -v -s -x

test-cc-o2:
	BP_TEST_CC_OPTIMIZATION=-O2 pytest test_encoding -v -s -x

test-optimization-mode:
	BP_TEST_OPTIMIZATION_ARG=-O pytest test_encoding -v -s -x

test: test-standard test-cc-o2 test-optimization-mode
