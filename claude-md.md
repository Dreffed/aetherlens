# CLAUDE.md - AI Assistant Development Guidelines

## Project Context

AetherLens Home Edition is an open-source cost and usage monitoring platform for home automation, IoT devices, and personal cloud services. This document provides context and guidelines for AI assistants (particularly Claude) when contributing to this project.

## Project Philosophy

- **Developer-First**: Prioritize developer experience and API clarity
- **Privacy-Focused**: All data stays local unless explicitly configured otherwise
- **Plugin-Driven**: Core should be minimal; functionality comes from plugins
- **Resource-Efficient**: Must run on Raspberry Pi 4 or equivalent
- **Observable**: Comprehensive logging and metrics for debugging

## Code Standards

### Language Preferences

**Core Engine**: Rust (preferred) or Go
- Rust for performance-critical paths
- Go acceptable for rapid prototyping
- Must compile to ARM64 and x86_64

**Plugin SDK**: Multiple language support
- Python for ease of development
- JavaScript/TypeScript for web integrations  
- Go/Rust for performance plugins

**Frontend**: TypeScript + React
- Vite for build tooling
- Tailwind CSS for styling
- Recharts/D3.js for visualizations

### Code Style

```rust
// Rust: Use descriptive names, avoid abbreviations
pub struct MetricCollector {
    pub interval_seconds: u32,
    pub retry_attempts: u8,
}

// NOT: pub struct MC { pub int_s: u32, pub rtry: u8 }
```

```typescript
// TypeScript: Explicit types, functional style preferred
interface DeviceMetric {
  timestamp: number;
  deviceId: string;
  powerWatts: number;
  costPerHour: number;
}

// Use const and arrow functions
const calculateDailyCost = (metrics: DeviceMetric[]): number => {
  return metrics.reduce((sum, m) => sum + m.costPerHour * 24, 0);
};
```

### Error Handling

- Never panic in production code
- All errors should be actionable
- Include context in error messages

```rust
// Good
return Err(format!("Failed to connect to device {}: {}", device_id, err));

// Bad  
return Err("Connection failed");
```

## Architecture Principles

### Data Flow
1. Collectors gather metrics from devices/services
2. Processors normalize and enrich data
3. Storage layer persists time-series data
4. API layer serves processed data
5. UI/Exporters consume via API

### Plugin Architecture
- Plugins run in isolated processes
- Communication via gRPC or message queue
- Plugins cannot crash the core
- Hot-reload capability required

### Security Requirements
- All external connections use TLS
- API keys stored in secure keyring
- Local authentication required
- Optional encryption at rest

## Testing Requirements

### Unit Tests
- Minimum 80% coverage for core
- All public APIs must have tests
- Mock external dependencies

### Integration Tests  
- Test plugin loading/unloading
- Verify data pipeline end-to-end
- Test error recovery

### Performance Benchmarks
- Memory usage under 256MB for core
- Sub-second plugin initialization
- Handle 1000+ metrics/second

## Documentation Standards

### Code Comments
```rust
/// Collects metrics from smart home devices at specified intervals.
/// 
/// # Arguments
/// * `config` - Device configuration including credentials
/// * `callback` - Function called with collected metrics
/// 
/// # Returns
/// * `Ok(())` on successful start
/// * `Err(CollectorError)` if initialization fails
/// 
/// # Example
/// ```
/// let collector = MetricCollector::new(config)?;
/// collector.start(|metric| process_metric(metric))?;
/// ```
pub fn start_collection(config: Config, callback: Fn) -> Result<()>
```

### API Documentation
- OpenAPI 3.0 specification required
- Include example requests/responses
- Document rate limits and quotas

## Common Patterns

### Metric Collection
```rust
pub trait MetricSource {
    fn collect(&self) -> Result<Vec<Metric>>;
    fn validate_config(&self) -> Result<()>;
    fn test_connection(&self) -> Result<()>;
}
```

### Cost Calculation
```typescript
interface CostCalculator {
  calculateCost(usage: Usage, rates: RateSchedule): Cost;
  optimizeCost(usage: Usage, constraints: Constraints): Optimization;
}
```

### Plugin Communication
```protobuf
message MetricRequest {
  string device_id = 1;
  int64 start_time = 2;
  int64 end_time = 3;
}

message MetricResponse {
  repeated Metric metrics = 1;
  string next_cursor = 2;
}
```

## Development Workflow

### Feature Development
1. Create issue describing feature
2. Write tests first (TDD)
3. Implement minimal solution
4. Refactor for clarity
5. Update documentation
6. Submit PR with tests passing

### Bug Fixes
1. Write test reproducing bug
2. Fix bug with minimal changes
3. Verify no regression
4. Document in CHANGELOG

### Plugin Development
1. Use plugin template
2. Implement required interfaces
3. Add configuration schema
4. Write integration tests
5. Document in plugin registry

## Performance Guidelines

### Memory Management
- Stream data when possible
- Use object pools for frequent allocations
- Clear caches periodically
- Monitor for memory leaks

### Database Optimization
- Batch writes (1000+ metrics)
- Use appropriate retention policies
- Index on common query patterns
- Partition by time

### Caching Strategy
- Cache expensive calculations
- Invalidate on configuration change
- Use TTL for external API data
- Monitor cache hit rates

## Debugging Helpers

### Logging Levels
- ERROR: Service degradation
- WARN: Potential issues
- INFO: State changes
- DEBUG: Detailed flow
- TRACE: All activity

### Metrics to Track
- Collection success/failure rates
- API response times
- Memory/CPU usage
- Plugin health status
- Queue depths

## Common Issues & Solutions

### Issue: High CPU Usage
- Check collection intervals (minimum 10s)
- Verify batch processing
- Profile hot paths
- Consider rate limiting

### Issue: Memory Growth
- Check for retained references
- Verify streaming is used
- Review cache sizes
- Monitor goroutine/thread counts

### Issue: Plugin Crashes
- Implement circuit breaker
- Add retry with backoff
- Isolate in separate process
- Log crash details

## Example Plugin Structure

```python
# Plugin: Shelly Smart Plug Monitor

class ShellyPlugin(BasePlugin):
    def __init__(self, config: Dict):
        self.devices = config['devices']
        self.poll_interval = config.get('poll_interval', 30)
        
    async def collect_metrics(self) -> List[Metric]:
        metrics = []
        for device in self.devices:
            data = await self.fetch_device_data(device)
            metrics.append(self.parse_metrics(data))
        return metrics
        
    def get_capabilities(self) -> List[str]:
        return ['power', 'energy', 'voltage', 'current']
```

## Questions to Ask When Developing

1. Will this run on a Raspberry Pi?
2. Can this handle 1000 devices?
3. What happens when the network fails?
4. How does this impact privacy?
5. Is this configuration intuitive?
6. Can this be unit tested?
7. Will users understand error messages?
8. Is there a simpler approach?

## Red Flags to Avoid

- ❌ Hardcoded credentials
- ❌ Synchronous blocking calls
- ❌ Unbounded memory growth
- ❌ Tight coupling between components
- ❌ Missing error handling
- ❌ SQL injection vulnerabilities
- ❌ Plaintext sensitive data
- ❌ Race conditions

## Version Compatibility

- Semantic versioning (MAJOR.MINOR.PATCH)
- Maintain backwards compatibility in minor versions
- Deprecate features for one major version
- Plugin API versioning independent of core

## Resources

- [Project Wiki](https://github.com/aetherlens/home/wiki)
- [Plugin Development Guide](./docs/PLUGIN_GUIDE.md)
- [API Reference](./docs/API.md)
- [Contributing Guidelines](./CONTRIBUTING.md)

## AI Assistant Notes

When generating code for this project:
1. Prioritize readability over cleverness
2. Include comprehensive error handling
3. Add tests alongside implementation
4. Consider resource constraints
5. Document non-obvious decisions
6. Use established patterns from codebase
7. Validate against schema definitions
8. Consider plugin boundaries

Remember: This is for home users who value privacy, control, and transparency. Every line of code should reflect these values.