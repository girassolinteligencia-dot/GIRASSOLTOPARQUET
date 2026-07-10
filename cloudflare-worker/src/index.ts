import { gerarLicencaWorker } from "./license";

export interface Env {
  LICENCAS_KV: KVNamespace;
  HOTMART_HOTTOK: string;
  LICENSE_PRIVATE_KEY: string;
  RESEND_API_KEY: string;
  EMAIL_REMETENTE?: string;
}

/**
 * Auxiliar para calcular SHA-256 de uma string usando Web Crypto.
 */
async function obterSha256(texto: string): Promise<string> {
  const buffer = new TextEncoder().encode(texto);
  const hashBuffer = await crypto.subtle.digest("SHA-256", buffer);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map(b => b.toString(16).padStart(2, "0")).join("");
}

/**
 * Envia o e-mail contendo o arquivo license.lic anexado via API do Resend.com.
 */
async function enviarEmailResend(
  emailDestino: string,
  licencaConteudo: string,
  transactionId: string,
  env: Env
): Promise<void> {
  const apiKey = env.RESEND_API_KEY;
  const remetente = env.EMAIL_REMETENTE || "licencas@girassolinteligencia.com.br";
  
  if (!apiKey) {
    console.error("Configuração de envio de e-mail ausente (RESEND_API_KEY).");
    throw new Error("Serviço de e-mail não configurado no servidor.");
  }

  if (apiKey === "mock" || apiKey === "MOCK") {
    console.info("Simulando envio de e-mail (chave mock/desenvolvimento).");
    return;
  }
  
  // Codificar o conteúdo do JSON da licença em base64 de forma segura (lidando com UTF-8)
  const bytes = new TextEncoder().encode(licencaConteudo);
  let binary = "";
  for (let i = 0; i < bytes.length; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  const base64License = btoa(binary);
  
  const response = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${apiKey}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      from: remetente,
      to: [emailDestino],
      subject: "Sua Licença do GIRASSOLtoPARQUET",
      text: `Olá,\n\nAgradecemos sua compra! Sua licença do GIRASSOLtoPARQUET foi gerada com sucesso.\n\nTransação: ${transactionId}\n\nPara ativar o aplicativo:\n1. Baixe o arquivo "license.lic" em anexo.\n2. Na tela de ativação do Conversor, clique em "Selecionar Arquivo..." e escolha o arquivo baixado.\n3. Clique em "Ativar Aplicativo".\n\nSe tiver qualquer dúvida ou problema, basta responder a este e-mail.\n\nAtenciosamente,\nEquipe Girassol Inteligência`,
      attachments: [
        {
          filename: "license.lic",
          content: base64License
        }
      ]
    })
  });
  
  if (!response.ok) {
    const errorText = await response.text();
    console.error(`Erro do Resend: ${response.status} - ${errorText}`);
    throw new Error(`Falha no envio de e-mail: ${response.status}`);
  }
}

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);
    
    // Validar rota e método
    if (url.pathname !== "/webhook/hotmart" || request.method !== "POST") {
      return new Response("Not Found", { status: 404 });
    }
    
    // 1. Validar Header X-HOTMART-HOTTOK
    const hottok = request.headers.get("X-HOTMART-HOTTOK");
    const hottokEsperado = env.HOTMART_HOTTOK;
    
    if (!hottokEsperado || hottok !== hottokEsperado) {
      console.warn("Bloqueado: Requisição de webhook com token inválido.");
      return new Response(JSON.stringify({ error: "Unauthorized" }), { 
        status: 401, 
        headers: { "Content-Type": "application/json" } 
      });
    }
    
    // Parsear payload
    let payloadData: any;
    try {
      payloadData = await request.json();
    } catch (e: any) {
      console.error("Falha ao ler JSON do payload:", e.message);
      return new Response(JSON.stringify({ error: "Invalid JSON" }), { 
        status: 400, 
        headers: { "Content-Type": "application/json" } 
      });
    }
    
    let event = payloadData.event;
    if (event) {
      event = event.toUpperCase();
    }
    
    // Extrair email e transaction_id de forma robusta
    const email = payloadData.data?.buyer?.email || payloadData.email;
    const transactionId = payloadData.data?.purchase?.transaction || payloadData.transaction_id || payloadData.transaction;
    
    if (!transactionId) {
      console.warn(`Evento ${event} ignorado: Ausência de transaction_id.`);
      return new Response(JSON.stringify({ status: "ignored", reason: "missing_transaction_id" }), { 
        status: 200, 
        headers: { "Content-Type": "application/json" } 
      });
    }
    
    // 2. Tratar eventos
    if (event === "PURCHASE_APPROVED") {
      if (!email) {
        console.error(`Falha: Transação ${transactionId} sem e-mail de comprador.`);
        return new Response(JSON.stringify({ error: "Email ausente" }), { 
          status: 400, 
          headers: { "Content-Type": "application/json" } 
        });
      }
      
      // Idempotência via KV
      const existente = await env.LICENCAS_KV.get(transactionId);
      if (existente) {
        console.info(`Transação ${transactionId} já processada anteriormente (idempotência).`);
        return new Response(JSON.stringify({ status: "ignored", reason: "already_processed", transaction_id: transactionId }), { 
          status: 200, 
          headers: { "Content-Type": "application/json" } 
        });
      }
      
      try {
        // Obter chave privada de secret
        const privateKey = env.LICENSE_PRIVATE_KEY;
        if (!privateKey) {
          throw new Error("LICENSE_PRIVATE_KEY não está configurada no Cloudflare.");
        }
        
        // Gerar a licença
        const licString = await gerarLicencaWorker(email, null, null, "perpetua", privateKey);
        const sha256 = await obterSha256(licString);
        
        // Enviar por e-mail via Resend
        await enviarEmailResend(email, licString, transactionId, env);
        
        // Salvar registro no KV
        const registro = {
          email: email,
          transaction_id: transactionId,
          timestamp: new Date().toISOString(),
          sha256_lic: sha256,
          status: "ativa"
        };
        await env.LICENCAS_KV.put(transactionId, JSON.stringify(registro));
        
        console.info(`Licença emitida e enviada com sucesso para ${email} (Transação: {transaction_id}).`);
        return new Response(JSON.stringify({ 
          status: "success", 
          transaction_id: transactionId, 
          email: email,
          license: licString 
        }), { 
          status: 200, 
          headers: { "Content-Type": "application/json" } 
        });
        
      } catch (err: any) {
        console.error(`Erro ao gerar/enviar licença para ${email}:`, err.message);
        return new Response(JSON.stringify({ error: err.message }), { 
          status: 500, 
          headers: { "Content-Type": "application/json" } 
        });
      }
      
    } else if (event === "PURCHASE_CANCELED" || event === "PURCHASE_REFUNDED") {
      // Obter registro existente do KV
      const registroStr = await env.LICENCAS_KV.get(transactionId);
      if (registroStr) {
        try {
          const registro = JSON.parse(registroStr);
          registro.status = "revogada";
          await env.LICENCAS_KV.put(transactionId, JSON.stringify(registro));
          console.info(`Licença vinculada à transação ${transactionId} foi REVOGADA no KV devido a evento ${event}.`);
          return new Response(JSON.stringify({ status: "revoked", transaction_id: transactionId }), { 
            status: 200, 
            headers: { "Content-Type": "application/json" } 
          });
        } catch (e) {
          console.error("Falha ao analisar JSON do registro para revogação:", e);
        }
      }
      
      console.info(`Evento de revogação ${event} ignorado: Nenhuma licença ativa encontrada para transação ${transactionId}.`);
      return new Response(JSON.stringify({ status: "ignored", reason: "transaction_not_found", transaction_id: transactionId }), { 
        status: 200, 
        headers: { "Content-Type": "application/json" } 
      });
      
    } else {
      console.info(`Evento ${event} recebido para transação ${transactionId} e ignorado.`);
      return new Response(JSON.stringify({ status: "ignored", reason: `unhandled_event_${event}`, transaction_id: transactionId }), { 
        status: 200, 
        headers: { "Content-Type": "application/json" } 
      });
    }
  }
};
