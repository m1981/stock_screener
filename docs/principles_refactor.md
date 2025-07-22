Here are the key practices to follow during architectural refactoring:

1. Incremental Changes
- Make small, manageable changes
- Keep the system working at all times
- Implement changes gradually

2. Clear Documentation
- Document architectural decisions (ADRs)
- Keep diagrams updated
- Document migration steps

4. Code Practices
- Follow SOLID principles
  - Single Responsibility: Each class/interface handles one concern
  - Open/Closed: Extend functionality through interfaces
  - Liskov Substitution: Implementations must be substitutable
  - Interface Segregation: Small, focused interfaces
  - Dependency Inversion: Depend on abstractions
- Use design patterns appropriately
- Maintain clean code

5. Interface Design
- Split large interfaces into smaller, focused ones
- Group related functionality
- Keep interfaces cohesive
- Use composition over inheritance
- Document interface contracts
