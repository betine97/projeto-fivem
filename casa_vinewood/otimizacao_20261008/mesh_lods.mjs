import fs from 'node:fs';
import { MeshoptSimplifier } from './vendor/meshopt_simplifier.mjs';
import { MeshoptEncoder } from './vendor/meshopt_encoder.mjs';
await Promise.all([MeshoptSimplifier.ready, MeshoptEncoder.ready]);
const file = process.argv[2];
const jobs = JSON.parse(fs.readFileSync(file, 'utf8'));
function read(path, Type) {
    const bytes = fs.readFileSync(path);
    return new Type(bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength));
}
for (const job of jobs) {
    const original = read(job.indices, Uint32Array);
    const positions = read(job.positions, Float32Array);
    const attributes = read(job.attributes, Float32Array);
    const results = [];
    for (const level of job.levels) {
        let indices = original.slice(), error = 0;
        if (level.ratio < 1 && original.length > 600) {
            [indices, error] = MeshoptSimplifier.simplifyWithAttributes(
                original, positions, 3, attributes, job.weights.length,
                job.weights, null, Math.max(60, Math.floor(original.length * level.ratio / 3) * 3),
                level.error, ['LockBorder']);
        }
        // Reorder triangles for GPU vertex reuse and compact all vertex streams
        // through this exact remap. No original position, UV or normal is altered.
        const [remap, count] = MeshoptEncoder.reorderMesh(indices, true, false);
        fs.writeFileSync(level.output + '.indices', Buffer.from(indices.buffer));
        fs.writeFileSync(level.output + '.remap', Buffer.from(remap.buffer));
        results.push({ count, error, triangles: indices.length / 3 });
    }
    fs.writeFileSync(job.result, JSON.stringify(results));
}
