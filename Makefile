MOCHA_OPTS=
REPORTER = dot

check: test

test: test-unit

test-unit:
	@NODE_ENV=test ./node_modules/.bin/mocha \
		--reporter $(REPORTER) \
		$(MOCHA_OPTS)

test-cov: lib-cov
	@EXPRESS_COV=1 $(MAKE) test REPORTER=html-cov > coverage.html

lib-cov:
	@jscoverage lib lib-cov

benchmark:
	@./support/bench

.PHONY: test test-unit test-acceptance benchmark
