import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    globals: true,
    environment: 'node',
    include: ['tests/**/*.test.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html', 'json', 'lcov'],
      include: [
        'src/compiler/parser/**/*.ts',
        'src/compiler/semantic/**/*.ts',
        'src/testing/**/*.ts',
        'src/debugger/**/*.ts',
      ],
      thresholds: {
        branches: 65,
        functions: 80,
        lines: 78,
        statements: 78,
      },
    },
  },
});
