pragma circom 2.1.6;

template Bits64() {
    signal input value;
    signal input bits[64];
    var acc = 0;
    var pow = 1;
    for (var i = 0; i < 64; i++) {
        bits[i] * (bits[i] - 1) === 0;
        acc += bits[i] * pow;
        pow *= 2;
    }
    value === acc;
}

template DigestEq4() {
    signal input left[4];
    signal input right[4];
    signal input left_bits[4][64];
    signal input right_bits[4][64];

    component lb0 = Bits64();
    component lb1 = Bits64();
    component lb2 = Bits64();
    component lb3 = Bits64();
    component rb0 = Bits64();
    component rb1 = Bits64();
    component rb2 = Bits64();
    component rb3 = Bits64();

    lb0.value <== left[0];
    lb1.value <== left[1];
    lb2.value <== left[2];
    lb3.value <== left[3];
    rb0.value <== right[0];
    rb1.value <== right[1];
    rb2.value <== right[2];
    rb3.value <== right[3];

    for (var i = 0; i < 64; i++) {
        lb0.bits[i] <== left_bits[0][i];
        lb1.bits[i] <== left_bits[1][i];
        lb2.bits[i] <== left_bits[2][i];
        lb3.bits[i] <== left_bits[3][i];
        rb0.bits[i] <== right_bits[0][i];
        rb1.bits[i] <== right_bits[1][i];
        rb2.bits[i] <== right_bits[2][i];
        rb3.bits[i] <== right_bits[3][i];
    }

    for (var j = 0; j < 4; j++) {
        left[j] === right[j];
    }
}

template AionDigestLimbClosure(n) {
    signal input expected_root_limbs[4];
    signal input final_root_limbs[4];
    signal input selected_hash_limbs[4];
    signal input output_hash_limbs[4];
    signal input replay_root_limbs[4];
    signal input expected_root_bits[4][64];
    signal input final_root_bits[4][64];
    signal input selected_hash_bits[4][64];
    signal input output_hash_bits[4][64];
    signal input replay_root_bits[4][64];
    signal input tamper_failed;
    signal input child_passed[n];

    component root_eq = DigestEq4();
    component output_eq = DigestEq4();
    component replay_eq = DigestEq4();

    for (var i = 0; i < 4; i++) {
        root_eq.left[i] <== expected_root_limbs[i];
        root_eq.right[i] <== final_root_limbs[i];
        output_eq.left[i] <== selected_hash_limbs[i];
        output_eq.right[i] <== output_hash_limbs[i];
        replay_eq.left[i] <== replay_root_limbs[i];
        replay_eq.right[i] <== final_root_limbs[i];
        for (var b = 0; b < 64; b++) {
            root_eq.left_bits[i][b] <== expected_root_bits[i][b];
            root_eq.right_bits[i][b] <== final_root_bits[i][b];
            output_eq.left_bits[i][b] <== selected_hash_bits[i][b];
            output_eq.right_bits[i][b] <== output_hash_bits[i][b];
            replay_eq.left_bits[i][b] <== replay_root_bits[i][b];
            replay_eq.right_bits[i][b] <== final_root_bits[i][b];
        }
    }

    tamper_failed === 1;
    for (var j = 0; j < n; j++) {
        child_passed[j] * (child_passed[j] - 1) === 0;
        child_passed[j] === 1;
    }
}

component main { public [
    expected_root_limbs,
    final_root_limbs,
    selected_hash_limbs,
    output_hash_limbs,
    replay_root_limbs
] } = AionDigestLimbClosure(8);
