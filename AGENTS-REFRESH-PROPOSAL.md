# AGENTS.md Smart Refresh Strategy

## Problema
- AGENTS.md desactualizado = planes incorrectos
- Recrear AGENTS.md cada vez = desperdicio de tokens
- Necesitamos saber CUÁNDO actualizar vs reusar

## Solución: Metadata + Freshness Score

### Metadata en AGENTS.md (footer)

```markdown
<!-- AGENTS_METADATA
version: 1.0.0
created_at: 2026-04-01T10:00:00Z
last_updated: 2026-04-05T15:30:00Z
base_commit: a1b2c3d
file_count: 150
key_files_checksum: abc123...
-->
```

### Algoritmo de Decisión

```python
def check_agents_md_freshness(service_path, agents_md_path):
    """
    Returns: (action, reason)
    action: CREATE | USE | REFRESH_REQUIRED | SUGGEST_REFRESH
    """
    if not os.path.exists(agents_md_path):
        return ("CREATE", "No existe AGENTS.md")
    
    metadata = extract_footer_metadata(agents_md_path)
    current_commit = get_latest_commit_hash(service_path)
    
    # 1. Sin cambios desde último update
    if metadata.base_commit == current_commit:
        return ("USE", "Sin cambios en codebase")
    
    # 2. Contar commits nuevos
    new_commits = count_commits_between(metadata.base_commit, current_commit)
    
    # 3. Detectar cambios críticos
    critical_changed = check_critical_files_changed(
        service_path, 
        metadata.base_commit, 
        current_commit
    )
    # Critical: models/, api/, config/, schema files
    
    # 4. Decision tree
    if critical_changed and new_commits > 5:
        return ("REFRESH_REQUIRED", 
                f"Cambios críticos detectados en {new_commits} commits")
    
    if new_commits > 20:
        return ("SUGGEST_REFRESH", 
                f"{new_commits} commits nuevos, posible desactualización")
    
    if new_commits > 5:
        # Cambios moderados, usar pero con disclaimer
        return ("USE_WITH_WARNING",
                f"{new_commits} commits nuevos, revisar manualmente")
    
    return ("USE", f"{new_commits} commits menores, AGENTS.md válido")
```

### Interacción con Usuario

**Caso A: Sin cambios**
```
✓ AGENTS.md está actualizado (commit a1b2c3d, sin cambios nuevos)
Continuando...
```

**Caso B: Cambios menores (< 5 commits)**
```
⚠ AGENTS.md tiene 3 commits nuevos (no críticos)
Usando existente para ahorrar tokens...
```

**Caso C: Sugerir refresh (5-20 commits)**
```
⚠ AGENTS.md está basado en commit a1b2c3d
   Hay 12 commits nuevos
   
¿Actualizar? (recomendado si hay cambios de arquitectura)
[y] yes - Actualizar AGENTS.md (consume tokens)
[n] no  - Usar existente (más rápido)
[d] diff - Ver cambios relevantes primero
```

**Caso D: Refresh requerido (> 20 commits o cambios críticos)**
```
⚠ AGENTS.md está desactualizado
   Base: commit a1b2c3d (hace 3 semanas)
   Actual: commit e4f5g6h (25 commits nuevos)
   
   Cambios críticos detectados:
   - src/models/payment.ts (modificado)
   - src/api/v2/routes.ts (nuevo)
   - database/schema.sql (modificado)

Actualizando AGENTS.md automáticamente...
```

## Implementación en Service Agent

### Wave 1 Modificado (Service Mapping)

```python
# Antes de escribir AGENTS.md
action, reason = check_agents_md_freshness(service_path, agents_md_path)

if action == "CREATE":
    # Crear nuevo
    write_agents_md(service_path, agents_md_path)
    
elif action == "USE" or action == "USE_WITH_WARNING":
    # Leer existente, no recrear
    if action == "USE_WITH_WARNING":
        append_note_to_summary("AGENTS.md puede estar ligeramente desactualizado")
    return existing_agents_md
    
elif action == "SUGGEST_REFRESH":
    # Preguntar al usuario (en discovery mode)
    # En plan mode, usar existente pero notificar
    user_wants_refresh = ask_user(f"{reason}. ¿Actualizar?")
    if user_wants_refresh:
        write_agents_md(service_path, agents_md_path)
    else:
        return existing_agents_md
        
elif action == "REFRESH_REQUIRED":
    # Forzar actualización
    write_agents_md(service_path, agents_md_path)
```

## Ventajas

| Aspecto | Beneficio |
|---------|-----------|
| **Tokens** | No recrear si está fresco |
| **Calidad** | Detectar cuando es crítico actualizar |
| **Transparencia** | Usuario sabe el estado del AGENTS.md |
| **Flexibilidad** | Puede forzar refresh si sospecha cambios |

## Comando Manual (opcional)

```bash
# Forzar refresh de AGENTS.md en servicios específicos
/agentbus-refresh-agents svc1 svc2
```

## Notas de Implementación

1. **Metadata liviana**: Solo un footer comentado, no afecta lectura
2. **Git commands**: `git rev-parse HEAD`, `git log --oneline`, `git diff --name-only`
3. **Critical files pattern**: `**/models/**`, `**/api/**`, `**/schema*`, `**/config/**`
4. **One-time per flow**: Nunca más de un refresh por servicio en un flujo
