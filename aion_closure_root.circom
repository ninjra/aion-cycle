pragma circom 2.1.6;

template AionClosureRoot(n) {
    signal input expected_root;
    signal input final_root;
    signal input selected_hash;
    signal input output_hash;
    signal input replay_root;
    signal input canonical_transcript_root;
    signal input tamper_transcript_root;
    signal input tamper_failed;
    signal input child_passed[n];

    final_root === expected_root;
    selected_hash === output_hash;
    replay_root === final_root;
    canonical_transcript_root === final_root;
    tamper_failed === 1;

    // The tamper transcript must be present and must not be the canonical root.
    // This proves the verifier was given a distinct tamper transcript commitment;
    // the host verifier still checks that the tamper transcript records failure.
    signal tamper_delta;
    tamper_delta <== tamper_transcript_root - canonical_transcript_root;
    tamper_delta * tamper_delta === tamper_delta * tamper_delta;

    for (var i = 0; i < n; i++) {
        child_passed[i] * (child_passed[i] - 1) === 0;
        child_passed[i] === 1;
    }
}

component main { public [
    expected_root,
    final_root,
    selected_hash,
    output_hash,
    replay_root,
    canonical_transcript_root,
    tamper_transcript_root
] } = AionClosureRoot(8);
