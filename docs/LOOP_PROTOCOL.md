# Protocolo de ejecución en loop

Cada ciclo de trabajo sigue exactamente estas etapas:

1. **SELECT**
   Elegir el siguiente ítem abierto de mayor dependencia/prioridad.

2. **SOURCE**
   Identificar la fuente upstream exacta y registrar versión/URL.

3. **INGEST**
   Copiar el recurso raw sin transformarlo.

4. **VERIFY**
   Verificar tamaño, integridad y checksum cuando sea técnicamente posible.

5. **REGISTER**
   Actualizar manifests y procedencia.

6. **DERIVE**
   Solo después del raw, generar datos normalizados/derivados.

7. **VALIDATE**
   Ejecutar schema/tests/consistencia.

8. **COMMIT**
   Guardar el bloque coherente en Git.

9. **STATUS**
   Actualizar STATUS.md:
   - completado;
   - en ejecución;
   - bloqueo;
   - siguiente.

10. **NEXT**
    Iniciar el siguiente bloque sin borrar tareas pendientes.

## Definición de DONE

Una fuente no está “copiada” hasta que:
- existe localmente;
- puede abrirse/reconstruirse;
- está registrada;
- conserva URL/procedencia;
- tiene checksum o explicación explícita de por qué todavía no;
- pasa las validaciones aplicables.

## Manejo de bloqueos

Cuando aparece un problema:
1. no se lo oculta;
2. se registra con ID B-xxx;
3. se describe impacto;
4. se define estrategia;
5. se trabaja alrededor solo si no compromete integridad;
6. luego se vuelve al bloqueo hasta cerrarlo.
