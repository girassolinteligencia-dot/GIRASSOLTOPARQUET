/**
 * Ordena as chaves do objeto alfabeticamente para produzir a mesma
 * serialização canônica JSON que o Python (json.dumps sort_keys=True).
 */
export function canonicalize(payload: any): string {
  const keys = Object.keys(payload).sort();
  const sortedObj: any = {};
  for (const key of keys) {
    let value = payload[key];
    if (value === undefined) {
      value = null;
    }
    sortedObj[key] = value;
  }
  return JSON.stringify(sortedObj);
}

/**
 * Converte a assinatura bruta de 64 bytes da API Web Crypto (formato IEEE P1363)
 * para o padrão ASN.1 DER esperado pela biblioteca python-cryptography no cliente.
 */
export function rawToDer(rawSignature: Uint8Array): Uint8Array {
  if (rawSignature.length !== 64) {
    throw new Error("A assinatura bruta deve conter exatamente 64 bytes para o P-256.");
  }
  
  let r = rawSignature.slice(0, 32);
  let s = rawSignature.slice(32, 64);
  
  // Remove zeros à esquerda (DER exige representação mínima)
  let rStart = 0;
  while (rStart < r.length - 1 && r[rStart] === 0) {
    rStart++;
  }
  r = r.slice(rStart);
  
  let sStart = 0;
  while (sStart < s.length - 1 && s[sStart] === 0) {
    sStart++;
  }
  s = s.slice(sStart);
  
  // Se o bit mais significativo estiver setado, prepend 0x00 (evita que seja tratado como negativo)
  if ((r[0] & 0x80) !== 0) {
    const newR = new Uint8Array(r.length + 1);
    newR.set(r, 1);
    r = newR;
  }
  if ((s[0] & 0x80) !== 0) {
    const newS = new Uint8Array(s.length + 1);
    newS.set(s, 1);
    s = newS;
  }
  
  const rLen = r.length;
  const sLen = s.length;
  
  // Tamanho total do conteúdo da sequência
  const totalLen = rLen + sLen + 4;
  
  const der = new Uint8Array(totalLen + 2);
  der[0] = 0x30; // Tag Sequence
  der[1] = totalLen;
  
  der[2] = 0x02; // Tag Integer
  der[3] = rLen;
  der.set(r, 4);
  
  const sOffset = 4 + rLen;
  der[sOffset] = 0x02; // Tag Integer
  der[sOffset + 1] = sLen;
  der.set(s, sOffset + 2);
  
  return der;
}

/**
 * Converte uma chave privada PEM para ArrayBuffer (formato DER).
 */
function pemToArrayBuffer(pem: string): ArrayBuffer {
  const cleanPem = pem
    .replace(/-----BEGIN[^-]*-----/g, "")
    .replace(/-----END[^-]*-----/g, "")
    .replace(/\s+/g, "");
    
  const binaryString = atob(cleanPem);
  const len = binaryString.length;
  const bytes = new Uint8Array(len);
  for (let i = 0; i < len; i++) {
    bytes[i] = binaryString.charCodeAt(i);
  }
  return bytes.buffer;
}

/**
 * Assina digitalmente uma licença em TypeScript.
 * Retorna o arquivo license.lic estruturado como JSON string.
 */
export async function gerarLicencaWorker(
  email: string,
  hardwareId: string | null,
  validade: string | null,
  tipo: string,
  privateKeyPem: string
): Promise<string> {
  // 1. Importar a chave privada
  const derBuffer = pemToArrayBuffer(privateKeyPem);
  const privateKey = await crypto.subtle.importKey(
    "pkcs8",
    derBuffer,
    {
      name: "ECDSA",
      namedCurve: "P-256"
    },
    false,
    ["sign"]
  );
  
  // 2. Definir datas
  const emitidaEm = new Date().toISOString().replace(/\.\d+Z$/, "Z");
  let expiraEm: string | null = null;
  
  if (tipo === "assinatura") {
    if (!validade) {
      throw new Error("Licenças do tipo 'assinatura' exigem uma data de validade (YYYY-MM-DD).");
    }
    expiraEm = `${validade}T23:59:59Z`;
  } else if (validade) {
    expiraEm = `${validade}T23:59:59Z`;
  }
  
  const payload = {
    email: email,
    hardware_id: hardwareId ? hardwareId.toUpperCase() : null,
    emitida_em: emitidaEm,
    expira_em: expiraEm,
    produto: "GIRASSOLtoPARQUET",
    versao_schema: 1
  };
  
  // 3. Serializar o payload canônico
  const canonicalPayload = canonicalize(payload);
  const payloadBytes = new TextEncoder().encode(canonicalPayload);
  
  // 4. Assinar
  const rawSignatureBuffer = await crypto.subtle.sign(
    {
      name: "ECDSA",
      hash: { name: "SHA-256" }
    },
    privateKey,
    payloadBytes
  );
  
  // 5. Converter assinatura bruta de 64 bytes para ASN.1 DER
  const derSignatureBytes = rawToDer(new Uint8Array(rawSignatureBuffer));
  
  // Converter assinatura DER para base64
  let binary = "";
  const len = derSignatureBytes.byteLength;
  for (let i = 0; i < len; i++) {
    binary += String.fromCharCode(derSignatureBytes[i]);
  }
  const signatureB64 = btoa(binary);
  
  // 6. Retornar JSON completo
  const licencaCompleta = {
    payload: payload,
    signature: signatureB64
  };
  
  return JSON.stringify(licencaCompleta, null, 2);
}
